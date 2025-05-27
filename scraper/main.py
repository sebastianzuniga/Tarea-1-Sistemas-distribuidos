import time
import json
import os
import logging
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    StaleElementReferenceException,
    WebDriverException
)

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s'
)
logging.getLogger('urllib3').setLevel(logging.ERROR)
logging.getLogger('selenium').setLevel(logging.ERROR)
logger = logging.getLogger(__name__)

class WazeScraper:
    def __init__(self, total_events_goal=10000):
        chrome_options = Options()
        # chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--lang=es')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        self.driver = webdriver.Chrome(
            service=ChromeService(), options=chrome_options
        )
        self.driver.set_page_load_timeout(30)
        self.driver.maximize_window()

        # Estado de eventos
        self.all_events = []            # lista de dicts
        self.seen_events = set()        # tuplas (tipo, direccion, tiempo)
        self.total_events_goal = total_events_goal
        self.storage_path = os.path.join(os.getcwd(), 'storage')
        os.makedirs(self.storage_path, exist_ok=True)

        # Patrón de desplazamiento en espiral
        self.pan_index = 0

        # Ocultar detección de Selenium
        self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        })
        logger.info('Scraper inicializado.')

    def close_event_popup(self):
        """Cierra popup de detalles si está abierto."""
        try:
            btn = self.driver.find_element(By.CSS_SELECTOR, 'a.leaflet-popup-close-button')
            btn.click()
            time.sleep(0.2)
        except Exception:
            pass

    def close_initial_popups(self):
        selectors = [
            (By.ID, 'CybotCookiebotDialogBodyButtonAccept'),
            (By.CSS_SELECTOR, 'button.waze-tour-tooltip__acknowledge'),
            (By.CSS_SELECTOR, 'i.w-icon-x.w-icon')
        ]
        for by, sel in selectors:
            try:
                WebDriverWait(self.driver, 3).until(
                    EC.element_to_be_clickable((by, sel))
                ).click()
                logger.info(f'Popup {sel} cerrado.')
                time.sleep(0.5)
            except Exception:
                pass

    def perform_zoom_in(self, levels=2):
        for i in range(levels):
            try:
                btn = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, '.leaflet-control-zoom-in'))
                )
                btn.click()
                logger.info(f'Zoom {i+1}/{levels}')
                time.sleep(0.3)
            except Exception:
                break

    def capture_icon(self, icon):
        """
        Hace click en un icono, extrae datos únicos y cierra popup.
        Evita duplicados comprobando seen_events.
        """
        try:
            # click y esperar detalles
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", icon)
            time.sleep(0.2)
            try:
                icon.click()
            except WebDriverException:
                self.driver.execute_script("arguments[0].click();", icon)

            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'wm-alert-details__time'))
            )
            tipo = self.driver.find_element(By.CLASS_NAME, 'wm-alert-details__title').text
            direccion = self.driver.find_element(By.CLASS_NAME, 'wm-alert-details__address').text
            tiempo = self.driver.find_element(By.CLASS_NAME, 'wm-alert-details__time').text
            key = (tipo, direccion, tiempo)
            if key in self.seen_events:
                return None

            reporter = self.driver.find_element(By.CLASS_NAME, 'wm-alert-details__reporter-name').text
            timestamp = time.strftime('%Y-%m-%dT%H:%M:%SZ')
            event = {
                'tipo': tipo,
                'direccion': direccion,
                'reportado_por': reporter,
                'tiempo': tiempo,
                'timestamp': timestamp
            }
            self.seen_events.add(key)
            return event
        except Exception as e:
            logger.debug(f'Error captura icono: {e}')
            return None
        finally:
            self.close_event_popup()

    def find_and_click_events(self):
        """
        Refresca lista de iconos y procesa nuevos eventos.
        """
        try:
            icons = self.driver.find_elements(By.CSS_SELECTOR, 'div.leaflet-marker-icon.wm-alert-icon')
            logger.info(f'Iconos detectados: {len(icons)}')
            count = 0
            for icon in icons:
                if len(self.all_events) >= self.total_events_goal:
                    break
                evt = self.capture_icon(icon)
                if evt:
                    self.all_events.append(evt)
                    count += 1
                    logger.info(f"Evento {len(self.all_events)}: {evt['tipo']} · {evt['direccion']}")
            return count
        except StaleElementReferenceException:
            return 0

    def pan_map_systematic(self):
        """
        Desplaza el mapa suavemente evitando out-of-bounds.
        """
        try:
            map_el = self.driver.find_element(By.CLASS_NAME, 'leaflet-container')
            size = map_el.size
            # offsets en 50% del ancho/alto
            dx = int(((self.pan_index % 4 == 1) - (self.pan_index % 4 == 3)) * size['width'] * 0.5)
            dy = int(((self.pan_index % 4 == 2) - (self.pan_index % 4 == 0)) * size['height'] * 0.5)
            ActionChains(self.driver).click_and_hold(map_el)
            ActionChains(self.driver).move_by_offset(dx, dy).release().perform()
            self.pan_index += 1
            time.sleep(1.5)
            logger.info(f'Desplazado dx={dx}, dy={dy}')
        except Exception as e:
            logger.warning(f'Pan sistemático fallido: {e}')
            self.pan_map_random()

    def pan_map_random(self):
        try:
            map_el = self.driver.find_element(By.CLASS_NAME, 'leaflet-container')
            size = map_el.size
            dx = random.randint(-size['width']//4, size['width']//4)
            dy = random.randint(-size['height']//4, size['height']//4)
            ActionChains(self.driver).drag_and_drop_by_offset(map_el, dx, dy).perform()
            logger.info(f'Pan aleatorio dx={dx}, dy={dy}')
            time.sleep(1)
        except Exception as e:
            logger.warning(f'Pan aleatorio fallido: {e}')

    def save_all_events_to_json(self):
        path = os.path.join(self.storage_path, 'eventos_waze.json')
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.all_events, f, ensure_ascii=False, indent=2)
        logger.info(f'Guardado JSON en {path}')

    def run(self):
        try:
            self.driver.get('https://www.waze.com/es-419/live-map/')
            time.sleep(3)
            self.close_initial_popups()
            self.perform_zoom_in()

            no_progress = 0
            while len(self.all_events) < self.total_events_goal:
                processed = self.find_and_click_events()
                if processed == 0:
                    no_progress += 1
                    if no_progress >= 2:
                        self.pan_map_systematic()
                        no_progress = 0
                    else:
                        time.sleep(1)
                else:
                    no_progress = 0
                    time.sleep(0.5)

            self.save_all_events_to_json()
        except KeyboardInterrupt:
            print("\nScraper detenido por el usuario. Guardando eventos...\n")
            self.save_all_events_to_json()
        finally:
            self.driver.quit()
            print("Ejecución finalizada.")

if __name__ == '__main__':
    scraper = WazeScraper(total_events_goal=10000)
    scraper.run()
