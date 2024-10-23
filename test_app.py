import unittest
from flask import url_for
from tr import app

class TestApp(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.app = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
        self.request_context = app.test_request_context()
        self.request_context.push()

    def tearDown(self):
        self.request_context.pop()
        self.app_context.pop()

    def test_status_endpoint(self):
        response = self.app.get(url_for('status'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"success": True, "version": "0", "status": "ok"})

    def test_index_redirect(self):
        response = self.app.get(url_for('index'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.location, url_for('forms', _external=True))

    def test_forms_endpoint(self):
        response = self.app.get(url_for('forms'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'forms.html', response.data)

    def test_education_adult_get(self):
        response = self.app.get(url_for('education_adult'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'education_adult.html', response.data)

    def test_education_adult_post(self):
        response = self.app.post(url_for('education_adult'), data={
            'studentname-lastname': 'Иванов',
            'studentname-name': 'Иван',
            'studentname-surname': 'Иванович',
            'studentbirth': '1990-01-01',
            'studentaddress': 'ул. Ленина, 1',
            'studentgender': 'male',
            'studentsnils': '123-456-789 01',
            'studentid-serial': '1234',
            'studentid-number': '567890',
            'studentid-by': 'УФМС',
            'studentid-issued': '2010-01-01',
            'studentbank': 'Сбербанк',
            'studentphone': '+79991234567',
            'studentemail': 'ivan@example.com',
            'examselection': '1',
            'examdate': '2023-12-31'
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"success": True, "message": "Form submitted successfully"})

    def test_exam_adult_get(self):
        response = self.app.get(url_for('exam_adult'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'exam_adult.html', response.data)

    def test_exam_adult_post(self):
        response = self.app.post(url_for('exam_adult'), data={
            'studentname-lastname': 'Петров',
            'studentname-name': 'Петр',
            'studentname-surname': 'Петрович',
            'studentbirth': '1985-05-05',
            'studentaddress': 'ул. Гагарина, 2',
            'studentgender': 'male',
            'studentsnils': '987-654-321 01',
            'studentid-serial': '4321',
            'studentid-number': '098765',
            'studentid-by': 'УФМС',
            'studentid-issued': '2005-05-05',
            'studentbank': 'ВТБ',
            'studentphone': '+79990987654',
            'studentemail': 'petr@example.com',
            'examselection': '2',
            'examdate': '2023-11-30'
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"success": True, "message": "Form submitted successfully"})

    def test_education_children_under14_get(self):
        response = self.app.get(url_for('education_children_under14'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'education_children_under14.html', response.data)

    def test_education_children_under14_post(self):
        response = self.app.post(url_for('education_children_under14'), data={
            'studentname-lastname': 'Сидоров',
            'studentname-name': 'Сидор',
            'studentname-surname': 'Сидорович',
            'studentbirth': '2010-01-01',
            'studentaddress': 'ул. Пушкина, 3',
            'studentgender': 'male',
            'studentsnils': '111-222-333 01',
            'studentid-serial': '1111',
            'studentid-number': '222222',
            'studentid-by': 'УФМС',
            'studentid-issued': '2015-01-01',
            'studentbank': 'Альфа-Банк',
            'studentphone': '+79993334444',
            'studentemail': 'sidor@example.com',
            'examselection': '3',
            'examdate': '2023-10-31',
            'clientname-lastname': 'Сидорова',
            'clientname-name': 'Анна',
            'clientname-surname': 'Петровна',
            'clientbirth': '1980-01-01',
            'clientaddress': 'ул. Пушкина, 3',
            'clientgender': 'female',
            'clientsnils': '444-555-666 01',
            'clientid-serial': '2222',
            'clientid-number': '333333',
            'clientid-by': 'УФМС',
            'clientid-issued': '2000-01-01',
            'clientbank': 'Альфа-Банк',
            'clientphone': '+79994445555',
            'clientemail': 'anna@example.com'
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"success": True, "message": "Form submitted successfully"})

    def test_education_children_over14_get(self):
        response = self.app.get(url_for('education_children_over14'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'education_children_over14.html', response.data)

    def test_education_children_over14_post(self):
        response = self.app.post(url_for('education_children_over14'), data={
            'studentname-lastname': 'Кузнецов',
            'studentname-name': 'Кузя',
            'studentname-surname': 'Кузнецович',
            'studentbirth': '2005-01-01',
            'studentaddress': 'ул. Гоголя, 4',
            'studentgender': 'male',
            'studentsnils': '777-888-999 01',
            'studentid-serial': '3333',
            'studentid-number': '444444',
            'studentid-by': 'УФМС',
            'studentid-issued': '2010-01-01',
            'studentbank': 'Альфа-Банк',
            'studentphone': '+79995556666',
            'studentemail': 'kuzya@example.com',
            'examselection': '4',
            'examdate': '2023-09-30',
            'clientname-lastname': 'Кузнецова',
            'clientname-name': 'Мария',
            'clientname-surname': 'Ивановна',
            'clientbirth': '1980-01-01',
            'clientaddress': 'ул. Гоголя, 4',
            'clientgender': 'female',
            'clientsnils': '555-666-777 01',
            'clientid-serial': '4444',
            'clientid-number': '555555',
            'clientid-by': 'УФМС',
            'clientid-issued': '2000-01-01',
            'clientbank': 'Альфа-Банк',
            'clientphone': '+79996667777',
            'clientemail': 'maria@example.com'
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"success": True, "message": "Form submitted successfully"})

    def test_exam_children_under14_get(self):
        response = self.app.get(url_for('exam_children_under14'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'exam_children_under14.html', response.data)

    def test_exam_children_under14_post(self):
        response = self.app.post(url_for('exam_children_under14'), data={
            'studentname-lastname': 'Николаев',
            'studentname-name': 'Николай',
            'studentname-surname': 'Николаевич',
            'studentbirth': '2012-01-01',
            'studentaddress': 'ул. Лермонтова, 5',
            'studentgender': 'male',
            'studentsnils': '222-333-444 01',
            'studentid-serial': '2222',
            'studentid-number': '333333',
            'studentid-by': 'УФМС',
            'studentid-issued': '2017-01-01',
            'studentbank': 'Сбербанк',
            'studentphone': '+79992223333',
            'studentemail': 'nikolay@example.com',
            'examselection': '5',
            'examdate': '2023-08-31',
            'clientname-lastname': 'Николаева',
            'clientname-name': 'Елена',
            'clientname-surname': 'Петровна',
            'clientbirth': '1980-01-01',
            'clientaddress': 'ул. Лермонтова, 5',
            'clientgender': 'female',
            'clientsnils': '666-777-888 01',
            'clientid-serial': '4444',
            'clientid-number': '555555',
            'clientid-by': 'УФМС',
            'clientid-issued': '2000-01-01',
            'clientbank': 'Сбербанк',
            'clientphone': '+79996667777',
            'clientemail': 'elena@example.com'
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"success": True, "message": "Form submitted successfully"})

    def test_exam_children_over14_get(self):
        response = self.app.get(url_for('exam_children_over14'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'exam_children_over14.html', response.data)

    def test_exam_children_over14_post(self):
        response = self.app.post(url_for('exam_children_over14'), data={
            'studentname-lastname': 'Михайлов',
            'studentname-name': 'Михаил',
            'studentname-surname': 'Михайлович',
            'studentbirth': '2007-01-01',
            'studentaddress': 'ул. Чехова, 6',
            'studentgender': 'male',
            'studentsnils': '333-444-555 01',
            'studentid-serial': '3333',
            'studentid-number': '444444',
            'studentid-by': 'УФМС',
            'studentid-issued': '2017-01-01',
            'studentbank': 'ВТБ',
            'studentphone': '+79993334444',
            'studentemail': 'mikhail@example.com',
            'examselection': '6',
            'examdate': '2023-07-31',
            'clientname-lastname': 'Михайлова',
            'clientname-name': 'Ольга',
            'clientname-surname': 'Ивановна',
            'clientbirth': '1980-01-01',
            'clientaddress': 'ул. Чехова, 6',
            'clientgender': 'female',
            'clientsnils': '777-888-999 01',
            'clientid-serial': '5555',
            'clientid-number': '666666',
            'clientid-by': 'УФМС',
            'clientid-issued': '2000-01-01',
            'clientbank': 'ВТБ',
            'clientphone': '+79997778888',
            'clientemail': 'olga@example.com'
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"success": True, "message": "Form submitted successfully"})

if __name__ == "__main__":
    unittest.main()