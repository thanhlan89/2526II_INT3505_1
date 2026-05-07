def validate_book_data(book_data):
    """Hàm kiểm tra dữ liệu sách hợp lệ"""
    if not book_data.get('title') or not str(book_data['title']).strip():
        return False  # Phải có tiêu đề
    if book_data.get('price') is None or book_data['price'] < 0:
        return False  # Giá không được âm
    return True