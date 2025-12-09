# habr_scraper_requests/scraper.py

import time
from fake_headers import Headers
import requests
from bs4 import BeautifulSoup


# Определение списка ключевых слов
KEYWORDS = ['дизайн', 'фото', 'web', 'python']


def fetch_page(url: str) -> str:
    """Получение HTML-страницы с обработкой ошибок и подменой заголовков."""
    headers = Headers(browser='chrome', os='win').generate()
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.text


def extract_preview_data(article) -> dict:
    """Извлечение preview-информации из карточки статьи."""
    # Получение заголовка и ссылки на статью
    title_tag = article.select_one('a.tm-title__link')
    if not title_tag:
        return {}
    title = title_tag.text.strip()
    link = 'https://habr.com' + title_tag['href']

    # Получение даты публикации
    time_tag = article.select_one('time')
    date = time_tag['datetime'] if time_tag else 'Неизвестно'

    # Получение teaser-текста статьи
    lead_tag = article.select_one('div.tm-article-snippet__lead')
    lead_text = lead_tag.get_text(strip=True) if lead_tag else ''

    # Получение хабов (тегов)
    hub_tags = article.select('a.tm-tags__tag')
    hubs = ' '.join(tag.get_text(strip=True).lower() for tag in hub_tags)

    return {
        'date': date,
        'title': title,
        'link': link,
        'preview_text': (title + ' ' + hubs + ' ' + lead_text).lower()
    }


def contains_keyword(text: str, keywords: list) -> bool:
    """Проверка наличия хотя бы одного ключевого слова в тексте (регистронезависимо)."""
    return any(word.lower() in text for word in keywords)


def fetch_full_article_text(article_url: str) -> str:
    """Получение полного текста статьи по ссылке."""
    try:
        html = fetch_page(article_url)
        soup = BeautifulSoup(html, features='lxml')
        article_body = soup.select_one('div.tm-article-body')
        if article_body:
            return article_body.get_text(strip=True).lower()
        return ''
    except (requests.exceptions.RequestException, Exception):
        return ''


def main():
    """Основная логика скраппинга."""
    print("Начинается парсинг статей на Хабре...\n")
    url = 'https://habr.com/ru/articles/'
    html = fetch_page(url)
    soup = BeautifulSoup(html, features='lxml')

    # Поиск всех карточек статей по устойчивому data-атрибуту
    articles = soup.select('article[data-test-id="articles-list-item"]')
    print(f"Найдено {len(articles)} статей на странице.\n")

    matching_articles = []

    # Перебор каждой статьи
    for article in articles:
        preview_data = extract_preview_data(article)
        if not preview_data:
            continue

        # Проверка наличия ключевых слов в preview-информации
        if contains_keyword(preview_data['preview_text'], KEYWORDS):
            # Дополнительная проверка наличия ключевых слов в полном тексте статьи
            full_text = fetch_full_article_text(preview_data['link'])
            if contains_keyword(full_text, KEYWORDS):
                matching_articles.append(preview_data)
                time.sleep(0.5)

    # Вывод результатов
    if matching_articles:
        print("\nНайдены статьи, содержащие ключевые слова:\n")
        for art in matching_articles:
            print(f"{art['date']} – {art['title']} – {art['link']}")
    else:
        print("Статьи с указанными ключевыми словами не найдены.")


if __name__ == '__main__':
    main()