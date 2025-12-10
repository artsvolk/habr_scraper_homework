import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException


# Определение списка ключевых слов
KEYWORDS = ['дизайн', 'фото', 'web', 'python']


def contains_keyword(text: str, keywords) -> bool:
    """Проверка наличия хотя бы одного ключевого слова в тексте (регистронезависимо)."""
    text_lower = text.lower()
    return any(word.lower() in text_lower for word in keywords)


def extract_preview_data(article_element):
    """Извлечение preview-информации из элемента статьи."""
    try:
        # Заголовок и ссылка
        title_element = article_element.find_element(By.CSS_SELECTOR, 'a.tm-title__link')
        title = title_element.text.strip()
        link = title_element.get_attribute('href')

        # Дата
        time_element = article_element.find_element(By.TAG_NAME, 'time')
        date = time_element.get_attribute('datetime')

        # Teaser
        try:
            lead_element = article_element.find_element(By.CSS_SELECTOR, 'div.tm-article-snippet__lead')
            lead_text = lead_element.text.strip()
        except NoSuchElementException:
            lead_text = ''

        # Хабы
        hub_elements = article_element.find_elements(By.CSS_SELECTOR, 'a.tm-tags__tag')
        hubs = ' '.join(tag.text.strip().lower() for tag in hub_elements)

        return {
            'date': date,
            'title': title,
            'link': link,
            'preview_text': title + ' ' + hubs + ' ' + lead_text
        }
    except (NoSuchElementException, WebDriverException):
        return {}


def get_full_article_text(driver, url: str) -> str:
    """Получение полного текста статьи по ссылке."""
    try:
        driver.get(url)
        WebDriverWait(driver, 5).until(
            expected_conditions.presence_of_element_located((By.CSS_SELECTOR, 'div.tm-article-body'))
        )
        body_element = driver.find_element(By.CSS_SELECTOR, 'div.tm-article-body')
        return body_element.text.strip()
    except (TimeoutException, NoSuchElementException, WebDriverException):
        return ''


def main():
    """Основная логика скраппинга на Selenium."""
    print("Начинается парсинг статей на Хабре (Selenium)...")

    # Настройка драйвера
    service = Service(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(service=service, options=options)

    try:
        driver.get('https://habr.com/ru/articles/')
        WebDriverWait(driver, 10).until(
            expected_conditions.presence_of_element_located((By.CSS_SELECTOR, 'article[data-test-id="articles-list-item"]'))
        )

        articles = driver.find_elements(By.CSS_SELECTOR, 'article[data-test-id="articles-list-item"]')
        print(f"Найдено {len(articles)} статей на странице.\n")

        matching_articles = []

        for article in articles:
            preview_data = extract_preview_data(article)
            if not preview_data:
                continue

            if contains_keyword(preview_data['preview_text'], KEYWORDS):
                full_text = get_full_article_text(driver, preview_data['link'])
                if contains_keyword(full_text, KEYWORDS):
                    matching_articles.append(preview_data)
                    time.sleep(0.5)

        if matching_articles:
            print("\nНайдены статьи, содержащие ключевые слова:\n")
            for art in matching_articles:
                print(f"{art['date']} – {art['title']} – {art['link']}")
        else:
            print("Статьи с указанными ключевыми словами не найдены.")

    except (TimeoutException, NoSuchElementException, WebDriverException):
        pass
    finally:
        driver.quit()


if __name__ == '__main__':
    main()