from hashlib import sha512

import requests
import json
import re
import traceback

'''
*
* get_payout_details_by_date method payout amount and dispay the payout response.
*
* param  string params - holds the request.POST form data.
* param  string merchant_key - holds the merchant key.
* param  string salt - holds the merchant salt key.
* param  string env - holds the env(enviroment)
*
* ##Return values
*
* - return array result - holds the refund array.
*
* @param  string params - holds the request.POST form data.
* @param  string merchant_key - holds the merchant key.
* @param  string salt - holds the merchant salt key.
* @param  string env - holds the env(enviroment)
*
* @return array result - holds the refund array.
*
'''
def get_payout_details_by_date(params, merchant_key, salt, env):
    try:
        result = _payout(params, merchant_key, salt, env)
        return result

    except Exception as e:
        traceback.print_exc()
        print("#######Error on payout:get_payout_details_by_date#######")
        return ({"status": False, "reason": 'Exception occured'});

'''
* _payout method use for initiate payout.
*
* param string key - holds the merchant key.
* param string merchant_email - holds the mrchant email.
* param string payout_date - holds the payout date.
*
* #### Define variable
*
* postedArray array - holds merchant key and _POST form data.
* URL        string - holds url based on the env(enviroment : 'test' or 'prod')
*
* ##Return values
*
* - return array payout_result - holds the response with status and data.
*
* - return integer status = 1 successful.
*
* - return integer status = 0 error.
*
* @param string key - holds the merchant key.
* @param string merchant_email - holds the merchant email.
* @param string payout_date - holds the payout date.
*
* @return array payout_result - holds the response with status and data.
* @return integer status = 1 successful.
* @return integer status = 0 error.
*
'''
def _payout(params, merchant_key, salt, env):
    postedArray = {}
    URL = None

    # argument validation
    argument_validation = _checkArgumentValidation(params, merchant_key, salt, env)
    if type(argument_validation) == type({}) and argument_validation['status'] == 0:
        return argument_validation

    # push merchant key into params dictionary.
    params._mutable = True
    params['merchant_key'] = merchant_key

    # remove white space, htmlentities(converts characters to HTML entities), prepared postedArray
    postedArray = _removeSpaceAndPreparePostArray(params)

    # type validation
    type_validation = _typeValidation(postedArray)
    if type_validation != True:
        return type_validation

    # empty validation
    empty_validation = _emptyValidation(postedArray, salt)
    if empty_validation != True:
        return empty_validation

    # email validation
    email_validation = _email_validation(postedArray['merchant_email'])
    if email_validation != True:
        return email_validation

    # get URL based on enviroment like (env = 'test' or env = 'prod')
    URL = _getURL(env)

    # process to start payout details
    refund_result = _payoutPayment(postedArray, salt, URL)

    return refund_result


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
      'merchant_key' : params['merchant_key'].strip(),
      'merchant_email' : params['merchant_email'].strip(),
      'payout_date' : params['payout_date'].strip()
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

    if not params['merchant_key']:
        empty_value = 'Merchant Key'

    if not params['merchant_email']:
        empty_value ='Merchant email'

    if not params['payout_date']:
        empty_value = 'Payout date'

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

    if not(isinstance(params['merchant_key'], str)):
        type_value = "Merchant Key should be string"

    if not(isinstance(params['merchant_email'], str)):
        type_value = "Merchant email should be string"

    if not(isinstance(params['payout_date'], str)):
        type_value = "Payout should be date"

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
* _payoutPayment method initiate payout payment.
*
* params array params_array - holds all form data with merchant key, transaction id etc.
* params string salt_key - holds the merchant salt key.
* params string url - holds the url based in env(enviroment type env = 'test' or env = 'prod')
*
* param string key - holds the merchant key.
* param string merchant_email - holds the mrchant email.
* param string payout_date - holds the payout date.
*
* ##Return values
*
* - return array with status and data - holds the details
*
* - return integer status = 0 means error.
*
* - return integer status = 1 means success and return result.
*
* @params array params_array - holds all form data with merchant key, merchant email, date etc.
* @params string salt_key - holds the merchant salt key.
* @params string url - holds the url based in env(enviroment type env = 'test' or env = 'prod')
*
* @param string key - holds the merchant key.
* @param string merchant_email - holds the merchant email.
* @param string payout_date - holds the payout date.
*
* @return array with status and data - holds the details
* @return integer status = 0 means error.
* @return integer status = 1 means success and go the url link.
*
'''
def _payoutPayment(params_array, salt_key, url):
    hash_key = None

    # generate hash key and push into params array.
    hash_key = _getHashKey(params_array, salt_key)
    params_array['hash'] = hash_key

    # requests call for retrive all payout
    request_result = requests.post(url + 'payout/v1/retrieve', params_array)
    result = json.loads(request_result.content)

    return result


'''
* _getHashKey method generate Hash key based on the API call (payout API).
*
* hash formate (hash sequence) :
*  hash = key|merchant_email|payout_date|salt
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
    hash_sequence = "merchant_key|merchant_email|payout_date"

    hash_sequence_array = hash_sequence.split("|")

    for value in hash_sequence_array:
        if value in posted:
            hash_string += str(posted[value])
        else:
            hash_string += ""
        hash_string += "|"

    hash_string += salt_key

    return  sha512(hash_string.encode('utf-8')).hexdigest().lower()
