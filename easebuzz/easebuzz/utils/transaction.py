from hashlib import sha512

import json
import re
import traceback

from easebuzz.easebuzz.utils.api_client import make_request

'''
*
* get_transaction_details method use for transaction
*
* param  string params - holds the request.POST form data.
* param  string merchant_key - holds the merchant key.
* param  string salt - holds the merchant salt key.
* param  string env - holds the env(enviroment)
*
* ##Return values
*
* - return array result - holds the single transaction details.
*
* @param  string params - holds the request.POST form data.
* @param  string merchant_key - holds the merchant key.
* @param  string salt - holds the merchant salt key.
* @param  string env - holds the env(enviroment)
*
* @return array result - holds the single transaction details.
*
'''
def get_transaction_details(params, merchant_key, salt, env):
    try:
        result = _transaction(params, merchant_key, salt, env)

        # verify transaction api response
        easebuzz_transaction_response =  _validateTransactionResponse(result, salt)
        return easebuzz_transaction_response

    except Exception as e:
        traceback.print_exc()
        print("#######Error on transaction:get_transaction_details#######")
        return ({"status": False, "reason": 'Exception occured'});


'''
* _transaction method use for get single transaction details.
*
* param string key - holds the merchant key.
* param string txnid - holds the transaction id.
* param string email - holds the email.
* param string amount - holds the amount.
* param string phone - holds the phone.
* param string hash - holds the hash key.
*
* #### Define variable
*
* postedArray array - holds merchant key and _POST form data.
*
* ##Return values
*
* - return array result - holds the response with status and data.
*
* - return integer status = 1 successful.
*
* - return integer status = 0 error.
*
* @param  string key - holds the merchant key.
* @param  string txnid - holds the transaction id.
* @param  string email - holds the email.
* @param  string amount - holds the amount.
* @param  string phone - holds the phone.
* @param  string hash - holds the hash key.
*
* @return array result - holds the response with status and data.
* @return integer status = 1 successful.
* @return integer status = 0 error.
*
'''
def _transaction(params, merchant_key, salt, env):
    postedArray = {}
    URL = None

    # argument validation
    argument_validation = _checkArgumentValidation(params, merchant_key, salt, env)
    if type(argument_validation) == type({}) and argument_validation['status'] == 0:
        return argument_validation

    # push merchant key into params dictionary.
    params._mutable = True
    params['key'] = merchant_key
    
    # remove white space, htmlentities(converts characters to HTML entities), prepared postedArray
    postedArray = _removeSpaceAndPreparePostArray(params)

    # empty validation
    empty_validation = _emptyValidation(postedArray, salt)
    if empty_validation != True:
        return empty_validation

    # check amount should be in floating formate
    if re.match(r"^([\d]+)\.([\d]?[\d])$", postedArray['amount']):
        postedArray['amount'] = float(postedArray['amount'])

    # type validation
    type_validation = _typeValidation(postedArray)
    if type_validation != True:
        return type_validation

    # email validation
    email_validation = _email_validation(postedArray['email'])
    if email_validation != True:
        return email_validation

    # get URL based on enviroment like (env = 'test' or env = 'prod')
    URL = _getURL(env)

    # process to start get transaction details
    transaction_result = _getTransaction(postedArray, salt, URL)

    return transaction_result


'''
*  _checkArgumentValidation method Check number of Arguments Validation. Means how many arguments submitted
*  from form and verify with
* API documentation.
*
* param  array *arg - holds the all request.POST data, merchant key, salt key and env.
*
* ##Return values
*
* - return interger 1 number of  arguments match.
*
* - return array status = 0 number of arguments mismatch.
*
* @param  array *arg - holds the all request.POST data, merchant key, salt key and env.
*
* @return interger 1 number of  arguments match.
* @return array status = 0 number of arguments mismatch.
*
* Note => *arg just like varargs method in java, It holds all parameters whenever call the method
*
'''
def _checkArgumentValidation(*arg):
    if len(arg) != 4 :
        return {
            'status' : 0,
            'data' : 'Invalid number of arguments.'
        }
    return True


'''
*  _removeSpaceAndPreparePostArray method Remove white space, converts characters to HTML entities
*   and prepared the posted array.
*
* param array params - holds request.POST array, merchand key and transaction key.
*
* ##Return values
*
* - return array temp_array - holds the all posted value after removing space.
*
* @param array params - holds request.POST array, merchand key and transaction key.
*
* @return array temp_array - holds the all posted value after removing space.
*
'''
def _removeSpaceAndPreparePostArray(params):

    temp_distionary = {
      'key' : params['key'].strip(),
      'txnid' : params['txnid'].strip(),
      'amount' : params['amount'].strip(),
      'email' : params['email'].strip(),
      'phone' : params['phone'].strip()
    }
    return temp_distionary


'''
* _emptyValidation method check empty validation for Mandatory Parameters.
*
* param  array params - holds the all _request.POST data
* param  string salt - holds the merchant salt key.
* param  string env - holds the enviroment.
*
* ##Return values
*
* - return boolean true - all params Mandatory parameters is not empty.
*
* - return array with status and data - params parameters or salt are empty.
*
* @param  array params - holds the all _request.POST data.
* @param  string salt - holds the merchant salt key.
* @param  string env - holds the enviroment.
*
* @return boolean true - all params Mandatory parameters is not empty.
* @return array with status and data - params parameters or salt are empty.
*
'''
def _emptyValidation(params, salt):
    empty_value = False

    if not params['key']:
        empty_value = 'Merchant Key'

    if not params['txnid']:
        empty_value = 'Transaction ID'

    if not params['amount']:
        empty_value = 'Transaction Amount'

    if not params['email']:
        empty_value ='Email'

    if not params['phone']:
        empty_value = 'Phone'

    if not salt:
        empty_value = 'Merchant Salt Key'

    if empty_value != False:
        return {
            'status' : 0,
            'data' : 'Mandatory Parameter '+ empty_value +' can not empty'
        }

    return True


'''
* _typeValidation method check type validation for field.
*
* param  array params - holds the all request.POST data.
* param  string salt - holds the merchant salt key.
* param  string env - holds the enviroment.
*
* ##Return values
*
* - return boolean true - all params parameters type are correct.
*
* - return array with status and data - params parameters type mismatch.
*
* @param  array params - holds the all request.POST data.
* @param  string salt - holds the merchant salt key.
* @param  string env - holds the enviroment.
*
* @return boolean true - all params parameters type are correct.
* @return array with status and data - params parameters type mismatch.
*
'''
def _typeValidation(params):

    type_value = False

    if not(isinstance(params['key'], str)):
        type_value = "Merchant Key should be string"

    if not(isinstance(params['txnid'], str)):
        type_value =  "Merchant Transaction ID should be string"

    if not(isinstance(params['amount'], float)):
        type_value = "The amount should float up to two or one decimal."

    if not(isinstance(params['phone'], str)):
        type_value = "Phone Number should be number"

    if not(isinstance(params['email'], str)):
        type_value = "Email should be string"

    if type_value != False:
        return {
           'status' : 0,
            'data' : type_value
        }

    return True


'''
* _email_validation method check email formate validation
*
* param string email - holds the email address.
*
* ##Return values
*
* - return boolean true - email formate is correct.
*
* - return array with status and data - email formate is incorrect.
*
* @param string email - holds the email address.
*
* @return boolean true - email formate is correct.
* @return array with status and data - email formate is incorrect.
*
'''
def _email_validation(email):

    if not re.match(r"^([\w\.-]+)@([\w-]+)\.([\w]{2,8})(\.[\w]{2,8})?", email):
        return {
            'status' : 0,
            'data' : 'Email invalid, Please enter valid email.'
        }
    return True


'''
* _getURL method set based on enviroment (env = 'test' or env = 'prod') and generate url link.
*
* param string env - holds the enviroment.
*
* ##Return values
*
* - return string url_link - holds the full url link.
*
* @param string env - holds the enviroment.
*
* @return string url_link - holds the full URL.
*
'''
def _getURL(env):
    url_link = None

    if env == 'test':
        url_link = "https://testdashboard.easebuzz.in/"
    elif env == 'prod':
        url_link = "https://dashboard.easebuzz.in/"
    else:
        url_link = "https://testdashboard.easebuzz.in/"

    return url_link


'''
* _getTransaction method get all details of a single transaction.
*
* params array params_array - holds all form data with merchant key, transaction id etc.
* params string salt_key - holds the merchant salt key.
* params string url - holds the url based in env(enviroment type env = 'test' or env = 'prod')
*
* param  string key - holds the merchant key.
* param  string txnid - holds the transaction id.
* param  string email - holds the email.
* param  float amount - holds the amount.
* param  string phone - holds the phone.
* param  string hash - holds the hash key.
*
* ##Return values
*
* - return array with status and data - holds the details
*
* - return integer status = 0 means error.
*
* - return integer status = 1 means success and go the url link.
*
* @params array params_array - holds all form data with merchant key, transaction id etc.
* @params string salt_key - holds the merchant salt key.
* @params string url - holds the url based in env(enviroment type env = 'test' or env = 'prod')
*
* @param  string key - holds the merchant key.
* @param  string txnid - holds the transaction id.
* @param  string email - holds the email.
* @param  float amount - holds the amount.
* @param  string phone - holds the phone.
* @param  string hash - holds the hash key.
*
* @return array with status and data - holds the details
* @return integer status = 0 means error.
* @return integer status = 1 means success and go the url link.
*
'''
def _getTransaction(params_array, salt_key, url):
    hash_key = None

    # generate hash key and push into params array.
    hash_key = _getHashKey(params_array, salt_key)

    params_array['hash'] = hash_key

    # Make API call with logging
    full_url = url + 'transaction/v1/retrieve'
    result = make_request(
        url=full_url,
        data=params_array,
        service="Transaction Retrieve",
        method="POST"
    )

    return result


'''
* _getHashKey method generate Hash key based on the API call (initiatePayment API).
*
* hash formate (hash sequence) :
*  hash = key|txnid|amount|email|phone|salt
*
* params string hash_sequence - holds the formate of hash key (sequence).
* params array params - holds the passed array.
* params string salt - holds merchand salt key.
*
* ##Return values
*
* - return string hash - holds the generated hash key.
*
* @params string hash_sequence - holds the formate of hash key (sequence).
* @params array params - holds the passed array.
* @params string salt - holds merchand salt key.
*
* @return string hash - holds the generated hash key.
*
'''
def _getHashKey(posted, salt_key):
    hash_string = ""
    hash_sequence = "key|txnid|amount|email|phone"

    hash_sequence_array = hash_sequence.split("|")

    for value in hash_sequence_array:
        if value in posted:
            hash_string += str(posted[value])
        else:
            hash_string += ""
        hash_string += "|"

    hash_string += salt_key

    return  sha512(hash_string.encode('utf-8')).hexdigest().lower()


'''
* _validateTransactionResponse method call response method for verify the response
*
* params array params_array - holds the passed array.
*
* ##Return values
*
* - return string URL result['status'] = 1 - means go to easebuzz page.
*
* - return string URL result['status'] = 0 - means error.
*
* @params array params_array - holds the passed array.
*
* @return string URL result['status'] = 1 - means go to easebuzz page.
* @return string URL result['status'] = 0 - means error
*
'''
def _validateTransactionResponse(response_array, salt_key):

    if response_array['status'] == True:

        # reverse hash key for validation means response is correct or not.
        reverse_hash_key = _getReverseHashKey(response_array['msg'], salt_key)

        if reverse_hash_key == response_array['msg']['hash']:

            return response_array

        else:
            return {
                'status' : 0,
                'data' : 'Hash key Mismatch'
            }

    return response_array


'''
* _getReverseHashKey to generate Reverse hash key for validation
*
* reverse hash formate (hash sequence) :
* reverse_hash = salt|response_array['status']|udf10|udf9|udf8|udf7|udf6|udf5|udf4|udf3|udf2|udf1|email|           *       firstname|productinfo|amount|txnid|key
*
* params string reverse_hash_sequence - holds the formate of reverse hash key (sequence).
* params object response_obj - holds the response object.
* params string s_key - holds the merchant salt key.
*
* ##Return values
*
* - return string  reverse_hash - holds the generated reverse hash key.
*
* @params string reverse_hash_sequence - holds the formate of reverse hash key (sequence).
* @params object  response_obj - holds the response object.
* @params string s_key - holds the merchant salt key.
*
* @return string  reverse_hash - holds the generated reverse hash key.
*
'''
def _getReverseHashKey(response_array, s_key):
    reverse_hash_string_sequence = "udf10|udf9|udf8|udf7|udf6|udf5|udf4|udf3|udf2|udf1|email|firstname|productinfo|amount|txnid|key"

    # make an array or split into array base on pipe sign.
    reverse_hash_string = ""

    hash_sequence_array = reverse_hash_string_sequence.split("|")
    reverse_hash_string += s_key + '|' + str(response_array['status'])

    for value in hash_sequence_array:
        reverse_hash_string += "|"
        if value in response_array:
            reverse_hash_string += str(response_array[value])
        else:
            reverse_hash_string += ""

    return  sha512(reverse_hash_string.encode('utf-8')).hexdigest().lower()


