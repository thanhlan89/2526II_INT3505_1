from book_validation import validate_book_data

def test_validate_book_data_hop_le():
    book = {"title": "Dế Mèn Phiêu Lưu Ký", "price": 50000}
    # Lệnh assert dùng để xác nhận kết quả trả về phải là True
    assert validate_book_data(book) is True

def test_validate_book_data_thieu_tieu_de():
    book = {"title": "   ", "price": 50000}
    assert validate_book_data(book) is False

def test_validate_book_data_gia_am():
    book = {"title": "Sách Python", "price": -10000}
    assert validate_book_data(book) is False