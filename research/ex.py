from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
import pandas as pd

# Настройки браузера
options = Options()
options.add_argument('--headless')  # если нужно скрытно
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

driver = webdriver.Chrome(options=options)

# Открываем страницу "Земля"
driver.get("https://www.olx.uz/nedvizhimost/zemlja/prodazha/")
time.sleep(5)  # Дать странице прогрузиться

# Открываем выпадающий фильтр "Расположение"
location_filter_button = driver.find_element(By.XPATH, '//div[.//span[text()="Расположение"]]//div[@role="button"]')
location_filter_button.click()
time.sleep(2)

# Собираем все пункты в открывшемся списке
locations = driver.find_elements(By.XPATH, '//ul//li//a[contains(@href, "/nedvizhimost/zemlja/prodazha/")]')

rayon_list = []
for loc in locations:
    name = loc.text.strip()
    href = loc.get_attribute("href")
    if name and "/prodazha/" in href:
        rayon = href.rstrip("/").split("/")[-1]  # последний кусок — это rayon_latin_name
        rayon_list.append({"name": name, "rayon_latin_name": rayon})

# Закрываем браузер
driver.quit()

# Сохраняем в Excel
df = pd.DataFrame(rayon_list)
df.to_excel("rayon_latin_names.xlsx", index=False)


print("✅ Список сохранён: rayon_latin_names.xlsx")
