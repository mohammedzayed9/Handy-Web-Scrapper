import sys
import csv
import re
import json
from urllib.error import URLError
from urllib.request import urlopen
from bs4 import BeautifulSoup
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QCheckBox, QFileDialog, \
    QMessageBox, QProgressBar
from PyQt5.QtCore import QThread, pyqtSignal
from openpyxl import Workbook


class ScrapeThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal()

    def __init__(self, url, scrape_photos, scrape_urls, scrape_emails, scrape_telephone_numbers, scrape_addresses):
        super().__init__()
        self.url = url
        self.scrape_photos = scrape_photos
        self.scrape_urls = scrape_urls
        self.scrape_emails = scrape_emails
        self.scrape_telephone_numbers = scrape_telephone_numbers
        self.scrape_addresses = scrape_addresses

    def run(self):
        self.data = []
        try:
            html = urlopen(self.url)
        except (URLError, ValueError):
            QMessageBox.critical(None, "Error", "Invalid URL or connection issue")
            self.finished.emit()
            return

        soup = BeautifulSoup(html, 'html.parser')

        total_steps = 0
        if self.scrape_photos:
            total_steps += 1
        if self.scrape_urls:
            total_steps += 1
        if self.scrape_emails:
            total_steps += 1
        if self.scrape_telephone_numbers:
            total_steps += 1
        if self.scrape_addresses:
            total_steps += 1

        current_step = 0

        if self.scrape_photos:
            try:
                self.scrape_photos_function(soup)
                current_step += 1
                self.progress.emit(int(current_step / total_steps * 100))
            except Exception as e:
                QMessageBox.critical(None, "Error", f"Error scraping photos: {str(e)}")

        if self.scrape_urls:
            try:
                self.scrape_urls_function(soup)
                current_step += 1
                self.progress.emit(int(current_step / total_steps * 100))
            except Exception as e:
                QMessageBox.critical(None, "Error", f"Error scraping URLs: {str(e)}")

        if self.scrape_emails:
            try:
                self.scrape_emails_function(soup)
                current_step += 1
                self.progress.emit(int(current_step / total_steps * 100))
            except Exception as e:
                QMessageBox.critical(None, "Error", f"Error scraping emails: {str(e)}")

        if self.scrape_telephone_numbers:
            try:
                self.scrape_telephone_numbers_function(soup)
                current_step += 1
                self.progress.emit(int(current_step / total_steps * 100))
            except Exception as e:
                QMessageBox.critical(None, "Error", f"Error scraping telephone numbers: {str(e)}")

        if self.scrape_addresses:
            try:
                self.scrape_addresses_function(soup)
                current_step += 1
                self.progress.emit(int(current_step / total_steps * 100))
            except Exception as e:
                QMessageBox.critical(None, "Error", f"Error scraping addresses: {str(e)}")

        self.finished.emit()

    def scrape_photos_function(self, soup):
        img_tags = soup.find_all('img')
        for img in img_tags:
            photo_url = img.get('src')
            if photo_url:
                self.data.append(['Photo', photo_url])

    def scrape_urls_function(self, soup):
        link_tags = soup.find_all('a')
        for link in link_tags:
            url = link.get('href')
            if url:
                self.data.append(['URL', url])

    def scrape_emails_function(self, soup):
        email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        email_matches = re.findall(email_regex, str(soup))
        for email in email_matches:
            self.data.append(['Email', email])

    def scrape_telephone_numbers_function(self, soup):
        phone_regex = r'(\+\d{1,2}\s?)?(\()?\d{3}(\))?[-\s]?\d{3}[-\s]?\d{4}'
        phone_matches = re.findall(phone_regex, str(soup))
        for phone in phone_matches:
            phone_number = ''.join(phone)
            self.data.append(['Telephone Number', phone_number])

    def scrape_addresses_function(self, soup):
        address_regex = r'\b\d{1,5}\s+([A-Za-z]+|[A-Za-z]+\s[A-Za-z]+)\b'
        address_matches = re.findall(address_regex, str(soup))
        for address in address_matches:
            full_address = ' '.join(address)
            self.data.append(['Address', full_address])


class WebScraper(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Web Scraper")
        layout = QVBoxLayout()

        self.url_label = QLabel("Enter URL:")
        self.url_input = QLineEdit()
        layout.addWidget(self.url_label)
        layout.addWidget(self.url_input)

        self.photo_checkbox = QCheckBox("Scrape Photos")
        self.url_checkbox = QCheckBox("Scrape URLs")
        self.email_checkbox = QCheckBox("Scrape Emails")
        self.telephone_checkbox = QCheckBox("Scrape Telephone Numbers")
        self.address_checkbox = QCheckBox("Scrape Addresses")
        layout.addWidget(self.photo_checkbox)
        layout.addWidget(self.url_checkbox)
        layout.addWidget(self.email_checkbox)
        layout.addWidget(self.telephone_checkbox)
        layout.addWidget(self.address_checkbox)

        self.scrape_button = QPushButton("Scrape")
        self.scrape_button.clicked.connect(self.start_scraping)
        layout.addWidget(self.scrape_button)

        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

        self.save_button = QPushButton("Save Data")
        self.save_button.clicked.connect(self.save_data)
        layout.addWidget(self.save_button)

        self.setLayout(layout)
        self.setFixedSize(450, 280)

    def start_scraping(self):
        url = self.url_input.text()
        scrape_photos = self.photo_checkbox.isChecked()
        scrape_urls = self.url_checkbox.isChecked()
        scrape_emails = self.email_checkbox.isChecked()
        scrape_telephone_numbers = self.telephone_checkbox.isChecked()
        scrape_addresses = self.address_checkbox.isChecked()

        try:
            html = urlopen(url)
        except (URLError, ValueError):
            QMessageBox.critical(None, "Error", "Invalid URL or connection issue")
            return

        self.scrape_thread = ScrapeThread(url, scrape_photos, scrape_urls, scrape_emails, scrape_telephone_numbers,
                                          scrape_addresses)
        self.scrape_thread.progress.connect(self.update_progress)
        self.scrape_thread.finished.connect(self.scraping_finished)
        self.scrape_thread.start()
        self.setWindowTitle("Web Scraper (Working on it)")
    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def scraping_finished(self):
        self.progress_bar.setValue(100)
        QMessageBox.information(None, "Finished", "Scraping completed successfully")
        self.setWindowTitle("Web Scraper")

    def save_data(self):
        file_dialog = QFileDialog()
        file_dialog.setDefaultSuffix('.csv')
        file_name, _ = file_dialog.getSaveFileName(self, 'Save Data', '',
                                                   'CSV Files (*.csv);;Excel Files (*.xlsx);;JSON Files (*.json)')

        if file_name:
            file_extension = file_name.split('.')[-1].lower()

            if file_extension == 'csv':
                self.save_to_csv(file_name)
            elif file_extension == 'xlsx':
                self.save_to_excel(file_name)
            elif file_extension == 'json':
                self.save_to_json(file_name)
            else:
                QMessageBox.warning(None, 'Error', 'Invalid file format selected')

    def save_to_csv(self, file_name):
        with open(file_name, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Type', 'Value'])
            writer.writerows(self.scrape_thread.data)

        QMessageBox.information(None, "Save", "Data saved to CSV file")

    def save_to_excel(self, file_name):
        workbook = Workbook()
        sheet = workbook.active
        sheet.append(['Type', 'Value'])

        for row in self.scrape_thread.data:
            sheet.append(row)

        workbook.save(file_name)
        QMessageBox.information(None, "Save", "Data saved to Excel file")

    def save_to_json(self, file_name):
        data_dict = {'data': []}
        for row in self.scrape_thread.data:
            data_dict['data'].append({'Type': row[0], 'Value': row[1]})

        with open(file_name, 'w') as file:
            json.dump(data_dict, file, indent=4)

        QMessageBox.information(None, "Save", "Data saved to JSON file")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    scraper = WebScraper()
    scraper.show()
    sys.exit(app.exec_())
