'''
* Easebuzz class manage all functionalities of easebuzz Payment Gateway
'''
import json

class Easebuzz:

    MERCHANT_KEY = ''
    SALT = ''
    ENV = ''

    '''
    *
    * initialised private variable for setup easebuzz payment gateway.
    *
    * @param  string key - holds the merchant key.
    * @param  string salt - holds the merchant salt key.
    * @param  string env - holds the env(enviroment). 
    *
    '''
    def __init__(self, key, salt, env):
        self.MERCHANT_KEY = key
        self.SALT = salt
        self.ENV = env


    '''
    *
    * initiatePaymentAPI function to integrate easebuzz for payment.
    *
    * http method used - POST
    *
    * param string txnid - holds the transaction id (which is auto generate using hash)
    * param array params - holds the request.POST data which is pass from the html form.
    *
    * ##Return values
    *
    * - return array ApiResponse['status']== 1 means successful.
    * 
    * - return array ApiResponse['status']== 0 means error.
    *
    * @param array params - holds the request.POST data which is pass from the html form.
    *
    * @return array ApiResponse['status']== 1 successful.
    * @return array ApiResponse['status']== 0 error.
    *
    * ##Helper methods for initiate payment(payment.php)
    *
    * - initiate_payment(arg1, arg2, arg3, arg4) :- call all method initiate payment and dispaly payment page.
    * 
    * - _payment(arg1, arg2, arg3, arg4) :- use for initiate payment.
    *
    * - _paymentResponse(arg1) :- use for show api response (like error, payment page etc.).
    *
    * - _checkArgumentValidation(arg1, arg2, arg3, arg4) :- check no. of argument validation.
    *
    * - _removeSpaceAndPreparePostArray(arg1) :- remove space, anonymous tag from the request.POST and prepare array.
    *
    * - _typeValidation(arg1, arg2, arg3) :- check type validation (like amount shoud be float etc).
    *
    * - _emptyValidation(arg1, arg2) :- check empty validation for Mandatory Parameters.
    *
    * - _email_validation(arg1) :- check email formate validation.
    *
    * - _getURL(arg1) :- get URL based on set enviroment.
    *
    * - _pay(arg1, arg2, arg3) :- initiate payment.
    *
    * ## below method call from _pay() method.
    *
    * -- _getHashKey(arg1, arg2) :- generate hash key based on hash sequence.
    *
    * -- _curlCall(arg1, arg2) :- initiate pay link.
    *
    * ## below method call from requests.post() method.
    *
    * Note :- Before call below method, install requests. if requests is already installed the go ahead.
    *
    * install with the help of : pip install requests
    *
    *
    '''
    def initiatePaymentAPI(self, params):
        from . import payment
        result = payment.initiate_payment(params, self.MERCHANT_KEY, self.SALT, self.ENV)
        return result.get("data")


    '''
    *
    * transactionAPI function to query for single transaction
    *
    * http method used - POST
    *
    * param array params - holds the request.POST data which is pass from the html form.
    *
    * ##Return values
    *
    * - return array ApiResponse['status']== 1 means successful.
    * 
    * - return array ApiResponse['status']== 0 means error.
    *
    * @param array params - holds the request.POST data which is pass from the html form.
    *
    * @return array ApiResponse['status']== 1 successful.
    * @return array ApiResponse['status']== 0 error.
    *
    * ##Helper methods for initiate transaction(transaction.php)
    *
    * - get_transaction_details(arg1, arg2, arg3, arg4) :- call all method initiate transaction.
    *
    * - _transaction(arg1, arg2, arg3, arg4) :- use for initiate transaction.
    *
    * - _validateTransactionResponse(arg1, arg2) :- use for verify api response is acceptable or not.
    *
    * - _checkArgumentValidation(arg1, arg2, arg3, arg4) :- check no. of argument validation.
    *
    * - _removeSpaceAndPreparePostArray(arg1) :- remove space, anonymous tag from the request.POST and prepare array.
    *
    * - _typeValidation(arg1, arg2, arg3) :- check type validation (like amount shoud be float etc).
    *
    * - _emptyValidation(arg1, arg2) :- check empty validation for Mandatory Parameters.
    *
    * - _email_validation(arg1) :- check email formate validation.
    *
    * - _getURL(arg1) :- get URL based on set enviroment.
    * 
    * - _getTransaction(arg1, arg2, arg3) :- initiate transaction.
    *
    * ## below method call from _getTransaction() method.
    *
    * -- _getHashKey(arg1, arg2) :- generate hash key based on hash sequence.
    *
    * -- requests.post(arg1, arg2) :- initiate transaction link.
    *
    * ## below method call from _validateTransactionResponse() method.
    *
    * -- _getReverseHashKey(arg1, arg2) :- generate reverse hash key for response verification.
    *
    '''
    def transactionAPI(self, params):
        from . import transaction

        result = transaction.get_transaction_details(params, self.MERCHANT_KEY, self.SALT, self.ENV)
        return json.dumps(result)


    '''
    *
    * transactionDateAPI function to transaction based on date.
    *
    * http method used - POST
    *
    * param array params - holds the request.POST data which is pass from the html form.
    *
    * ##Return values
    *
    * - return array ApiResponse['status']== 1 means successful.
    * 
    * - return array ApiResponse['status']== 0 means error.
    *
    * @param array params - holds the request.POST data which is pass from the html form.
    *
    * @return array ApiResponse['status']== 1 successful.
    * @return array ApiResponse['status']== 0 error.
    *
    * ##Helper methods for initiate date transaction(transaction_date.php)
    *
    * - get_transactions_by_date(arg1, arg2, arg3, arg4) :- call all method initiate date transaction.
    *
    * - _date_transaction(arg1, arg2, arg3, arg4) :- use for initiate date transaction.
    *
    * - _checkArgumentValidation(arg1, arg2, arg3, arg4) :- check no. of argument validation.
    *
    * - _removeSpaceAndPreparePostArray(arg1) :- remove space, anonymous tag from the request.POST and prepare     array.
    *
    * - _typeValidation(arg1, arg2, arg3) :- check type validation (like amount shoud be float etc).
    *
    * - _emptyValidation(arg1, arg2) :- check empty validation for Mandatory Parameters.
    *
    * - _email_validation(arg1) :- check email formate validation.
    *
    * - _getURL(arg1) :- get URL based on set enviroment.
    * 
    * - _getDateTransaction(arg1, arg2, arg3) :- initiate date transaction.
    *
    * ## below method call from _getDateTransaction() method.
    *
    * -- _getHashKey(arg1, arg2) :- generate hash key based on hash sequence.
    *
    * -- requests.post(arg1, arg2) :- initiate transaction date link.
    *
    '''
    def transactionDateAPI(self, params):
        from . import transaction_date
        result = transaction_date.get_transactions_by_date(params, self.MERCHANT_KEY, self.SALT, self.ENV)
        return json.dumps(result)


    '''
    *
    * refundAPI function to refund for the transaction
    *
    * http method used - POST
    *
    * param array params - holds the request.POST data which is pass from the html form.
    *
    * ##Return values
    *
    * - return array ApiResponse['status']== 1 means successful.
    * 
    * - return array ApiResponse['status']== 0 means error.
    *
    * @param array params - holds the request.POST data which is pass from the html form.
    *
    * @return array ApiResponse['status']== 1 successful.
    * @return array ApiResponse['status']== 0 error.
    *
    * ##Helper methods for initiate refund (refund.php)
    *
    * - initiate_refund(arg1, arg2, arg3, arg4) :- call all method initiate refund.
    *
    * - _refund(arg1, arg2, arg3, arg4) :- use for initiate refund.
    *
    * - _checkArgumentValidation(arg1, arg2, arg3, arg4) :- check no. of argument validation.
    *
    * - _removeSpaceAndPreparePostArray(arg1) :- remove space, anonymous tag from the request.POST and prepare array.
    *
    * - _typeValidation(arg1, arg2, arg3) :- check type validation (like amount shoud be float etc).
    *
    * - _emptyValidation(arg1, arg2) :- check empty validation for Mandatory Parameters.
    *
    * - _email_validation(arg1) :- check email formate validation.
    *
    * - _getURL(arg1) :- get URL based on set enviroment.
    * 
    * - _refundPayment(arg1, arg2, arg3) :- initiate refund.
    *
    * ## below method call from _refundPayment() method.
    *
    * -- _getHashKey(arg1, arg2) :- generate hash key based on hash sequence.
    *
    * -- requests.post(arg1, arg2) :- initiate refund link.
    *
    '''
    def refundAPI(self, params):
        from . import refund
        result = refund.initiate_refund(params, self.MERCHANT_KEY, self.SALT, self.ENV)
        return json.dumps(result)


    '''
    *
    * payoutAPI function to payout for particular date.
    *
    * http method used - POST
    *
    * param array params - holds the request.POST data which is pass from the html form.
    *
    * ##Return values
    *
    * - return array ApiResponse['status']== 1 means successful.
    * 
    * - return array ApiResponse['status']== 0 means error.
    *
    * @param array params - holds the request.POST data which is pass from the html form.
    *
    * @return array ApiResponse['status']== 1 successful.
    * @return array ApiResponse['status']== 0 error.
    *
    * ##Helper methods for initiate payout (payout.php)
    *
    * - get_payout_details_by_date(arg1, arg2, arg3, arg4) :- call all method initiate payout.
    *
    * - _payout(arg1, arg2, arg3, arg4) :- use for initiate payout.
    *
    * - _checkArgumentValidation(arg1, arg2, arg3, arg4) :- check no. of argument validation.
    *
    * - _removeSpaceAndPreparePostArray(arg1) :- remove space, anonymous tag from the request.POST and prepare array.
    *
    * - _typeValidation(arg1, arg2, arg3) :- check type validation (like amount shoud be float etc).
    *
    * - _emptyValidation(arg1, arg2) :- check empty validation for Mandatory Parameters.
    *
    * - _email_validation(arg1) :- check email formate validation.
    *
    * - _getURL(arg1) :- get URL based on set enviroment.
    * 
    * - _payoutPayment(arg1, arg2, arg3) :- initiate payout payment.
    *
    * ## below method call from _payoutPayment() method.
    *
    * -- _getHashKey(arg1, arg2) :- generate hash key based on hash sequence.
    *
    * -- requests.post(arg1, arg2) :- initiate payout link.
    *
    '''
    def payoutAPI(self, params):
        from . import payout
        result = payout.get_payout_details_by_date(params, self.MERCHANT_KEY, self.SALT, self.ENV)
        return json.dumps(result)


    '''
    *
    * easebuzzResponse mehod to verify easebuzz API response is acceptable or not.
    *
    * http method used - POST
    *
    * - params array params - holds the API response array.
    * 
    * ##Return values
    *
    * - return array result- holds the API response array after verification of response. 
    *
    * @params array params - holds the API response array.
    *
    * @return array result- holds the API response array after verification of response.
    * 
    * ##Helper methods for display API response(payment.php) 
    *
    * - response(arg1, arg2) :- verify API response and retrun response array.
    *
    * - _removeSpaceAndPrepareAPIResponseArray(arg1) :- remove space, anonymous tag from the API response
    *                                                   array and prepare API response array. 
    *
    * - _emptyValidation(arg1, arg2) :- check empty validation in API response array.
    *
    * - _getResponse(arg1, arg2) :- check response is correct or not.
    *
    * ## below method call from _getResponse() method.
    * 
    * -- _getReverseHashKey(arg1, arg2) :- generate reverse hash key for validation.
    *
    '''
    def easebuzzResponse(self, params):
        from . import payment
        result = payment.easebuzzResponse(params, self.SALT)
        return json.dumps(result)

        