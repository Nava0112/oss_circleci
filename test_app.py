import pytest
from oss import app
from unittest.mock import patch, MagicMock

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_customer_login_page_loads(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b'Customer' in response.data or b'Login' in response.data

def test_supplier_login_page_loads(client):
    response = client.get('/login_supplier')
    assert response.status_code == 200
    assert b'Supplier' in response.data or b'Login' in response.data

def test_redirect_if_not_logged_in(client):
    response = client.get('/products', follow_redirects=False)
    assert response.status_code == 302
    assert '/' in response.headers['Location']

@patch('oss.get_db_connection')
def test_invalid_customer_login(mock_conn, client):
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = None
    mock_conn.return_value.cursor.return_value = mock_cursor

    response = client.post('/', data={
        'CustomerID': '999',
        'CustomerName': 'fakeuser'
    }, follow_redirects=True)
    assert b'Invalid' in response.data

@patch('oss.get_db_connection')
def test_products_page_redirect(mock_conn, client):
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = []
    mock_conn.return_value.cursor.return_value = mock_cursor

    response = client.get('/products', follow_redirects=False)
    assert response.status_code == 302

def test_add_customer_form_loads(client):
    response = client.get('/add_customer')
    assert response.status_code == 200
