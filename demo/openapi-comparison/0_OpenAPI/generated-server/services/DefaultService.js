/* eslint-disable no-unused-vars */
const Service = require('./Service');

/**
* Lấy danh sách sách
*
* returns List
* */
const booksGET = () => new Promise(
  async (resolve, reject) => {
    try {
      resolve(Service.successResponse({
      }));
    } catch (e) {
      reject(Service.rejectResponse(
        e.message || 'Invalid input',
        e.status || 405,
      ));
    }
  },
);
/**
* Thêm sách mới
*
* book Book 
* no response value expected for this operation
* */
const booksPOST = ({ book }) => new Promise(
  async (resolve, reject) => {
    try {
      resolve(Service.successResponse({
        book,
      }));
    } catch (e) {
      reject(Service.rejectResponse(
        e.message || 'Invalid input',
        e.status || 405,
      ));
    }
  },
);

module.exports = {
  booksGET,
  booksPOST,
};
