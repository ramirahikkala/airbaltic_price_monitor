#!/usr/bin/env python3
"""
Air Balticin hintaseuranta - seuraa lennon hintoja ja lähettää ne Home Assistantiin
"""

import os
import json
import requests
import time
import logging
from datetime import datetime
from typing import Optional, Dict

# Konfiguraatio
CONFIG_FILE = "config.json"
DATA_FILE = "price_history.json"
LOG_FILE = "price_tracker.log"

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class AirBalticPriceTracker:
    """Air Balticin hintaseuranta Home Assistantiin integroinnilla"""
    
    def __init__(self, config_file: str = CONFIG_FILE):
        self.config = self.load_config(config_file)
        self.price_history = self.load_history()
        self.ha_url = self.config.get('home_assistant', {}).get('url')
        self.ha_token = self.config.get('home_assistant', {}).get('token')
        
    def load_config(self, config_file: str) -> Dict:
        """Lataa konfiguraation"""
        if not os.path.exists(config_file):
            raise FileNotFoundError(f"Konfiguraatiotiedosto {config_file} puuttuu!")
        
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def load_history(self) -> Dict:
        """Lataa hintahistorian"""
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"prices": [], "notifications": []}
    
    def save_history(self):
        """Tallentaa hintahistorian"""
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.price_history, f, indent=2, ensure_ascii=False)
    
    def get_current_price(self) -> Optional[Dict]:
        """Hakee oikeat hinnat Air Balticista"""
        try:
            from playwright.sync_api import sync_playwright
            import re
            
            logger.info(f"Haetaan hintaa: {self.config['origin']} → {self.config['destination']}")
            
            url = (f"https://www.airbaltic.com/fi/varaa-lennot?"
                   f"tripType=return"
                   f"&originCode={self.config['origin']}"
                   f"&destinCode={self.config['destination']}"
                   f"&numAdt={self.config['passengers']}"
                   f"&selectedMonth={self.config['month']}")
            
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.set_viewport_size({"width": 1920, "height": 1080})
                
                try:
                    page.goto(url, wait_until="networkidle", timeout=60000)
                    page.wait_for_selector("[class*='price']", timeout=30000)
                    
                    prices = page.locator("[class*='price']").all()
                    if not prices:
                        logger.warning("Hinnan elementtejä ei löydetty")
                        browser.close()
                        return None
                    
                    price_text = prices[0].text_content()
                    
                    # Parse hinta (158€ tai 245,00€ -> 245.00)
                    match = re.search(r'(\d+)[.,]?(\d*)', price_text)
                    if match:
                        whole = match.group(1)
                        decimal = match.group(2) if match.group(2) else "00"
                        price = float(f"{whole}.{decimal}")
                    else:
                        logger.error(f"Hinnan parsinta epäonnistui: {price_text}")
                        browser.close()
                        return None
                    
                    browser.close()
                    logger.info(f"Hinta: {price:.2f} EUR")
                    
                    return {
                        'price': round(price, 2),
                        'currency': 'EUR',
                        'timestamp': datetime.now().isoformat(),
                    }
                    
                except Exception as e:
                    logger.error(f"Sivun käsittelyssä virhe: {e}")
                    browser.close()
                    return None
            
        except ImportError:
            logger.error("Playwright ei ole asennettu. Asenna: uv sync")
            return None
        except Exception as e:
            logger.error(f"Virhe hinnan haussa: {e}")
            return None
    
    def check_price_change(self, current_price: Dict) -> Optional[Dict]:
        """Tarkistaa, onko hinta muuttunut"""
        if not self.price_history['prices']:
            logger.info("Ensimmäinen hintamittaus")
            return None
        
        last_price_entry = self.price_history['prices'][-1]
        last_price = last_price_entry['price']
        current = current_price['price']
        
        if last_price != current:
            change = current - last_price
            change_percent = (change / last_price) * 100 if last_price > 0 else 0
            
            notification = {
                'timestamp': datetime.now().isoformat(),
                'old_price': last_price,
                'new_price': current,
                'change': change,
                'change_percent': round(change_percent, 2),
                'currency': current_price['currency']
            }
            
            return notification
        
        return None
    
    def send_email_notification(self, data: Dict) -> bool:
        """Lähettää hinnan Home Assistantiin"""
        if not self.ha_url or not self.ha_token:
            return False
        
        try:
            headers = {
                'Authorization': f'Bearer {self.ha_token}',
                'Content-Type': 'application/json'
            }
            
            # Tarkista onko kyseessä notification vai hintatietue
            if 'new_price' in data:
                # Muutos-notifikaatio
                state_value = f"{data['new_price']:.2f}"
                attributes = {
                    'currency': data['currency'],
                    'unit_of_measurement': '€',
                    'icon': 'mdi:airplane',
                    'friendly_name': f"{self.config['origin']} → {self.config['destination']}",
                    'last_updated': datetime.now().isoformat(),
                    'change': data['change'],
                    'change_percent': data['change_percent'],
                }
            else:
                # Normaali hintatietue
                state_value = f"{data['price']:.2f}"
                attributes = {
                    'currency': data['currency'],
                    'unit_of_measurement': '€',
                    'icon': 'mdi:airplane',
                    'friendly_name': f"{self.config['origin']} → {self.config['destination']}",
                    'last_updated': datetime.now().isoformat(),
                }
            
            # HA:n REST API endpoint
            entity_id = f"sensor.airbaltic_{self.config['origin'].lower()}_{self.config['destination'].lower()}_price"
            
            url = f"{self.ha_url}/api/states/{entity_id}"
            
            payload = {
                'state': state_value,
                'attributes': attributes
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            
            if response.status_code in [200, 201]:
                logger.info(f"✅ Hinta lähetetty HA:hin: {state_value} €")
                return True
            else:
                logger.warning(f"HA vastaus: {response.status_code}")
                return False
            
        except Exception as e:
            logger.error(f"Virhe HA:hin lähettäessä: {e}")
            return False
    
    def run_tracking_cycle(self) -> bool:
        """Suorittaa yhden seurantasyklin"""
        current_price = self.get_current_price()
        
        if current_price is None:
            logger.warning("Hinnan haku epäonnistui")
            return False
        
        # Tallenna hinta historiaan
        self.price_history['prices'].append(current_price)
        
        # Lähetä Home Assistantiin
        self.send_email_notification(current_price)
        
        # Tarkista muutokset
        notification = self.check_price_change(current_price)
        
        if notification:
            logger.info(f"⚠️  HINTA MUUTTUI: {notification['old_price']} → {notification['new_price']} EUR ({notification['change_percent']:+.1f}%)")
            self.price_history['notifications'].append(notification)
            # Lähetä muutos HA:hin
            self.send_email_notification(notification)
        else:
            logger.info(f"Hinta stabiili: {current_price['price']} {current_price['currency']}")
        
        self.save_history()
        return True
    
    def start_monitoring(self):
        """Aloittaa jatkuvan seurannan"""
        logger.info("="*60)
        logger.info(f"Hintaseuranta käynnissä: {self.config['origin']} → {self.config['destination']}")
        logger.info(f"Tarkistusväli: {self.config['check_interval']}s")
        
        if self.ha_url:
            logger.info(f"Home Assistant: {self.ha_url}")
        
        logger.info("="*60)
        
        try:
            cycle = 0
            while True:
                cycle += 1
                logger.info(f"\n[Sykli {cycle}]")
                self.run_tracking_cycle()
                
                logger.info(f"Seuraava {self.config['check_interval']}s päästä...")
                time.sleep(self.config['check_interval'])
        except KeyboardInterrupt:
            logger.info("\n⏹️  Seuranta pysäytetty")
        except Exception as e:
            logger.error(f"Virhe seurannassa: {e}")
            raise


def main():
    """Pääohjelma"""
    try:
        tracker = AirBalticPriceTracker()
        tracker.start_monitoring()
    except FileNotFoundError as e:
        logger.error(f"Virhe: {e}")
        print(f"\nVirhe: {e}")
        print("Luo config.json-tiedosto. Esimerkki on config.example.json-tiedostossa.")


if __name__ == "__main__":
    main()
