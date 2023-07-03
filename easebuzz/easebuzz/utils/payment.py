from hashlib import sha512

import requests
import json
import re
import traceback

# import webbrowser

'''
* initiate_payment method initiate payment and call dispay the payment page.
*
* param  string params - holds the request.POST form data.
* param  string merchant_key - holds the merchant key.
* param  string salt - holds the merchant salt key.
* param  string env - holds the env(enviroment)
*
* ##Return values
*
* - return array result - holds the payment link and status.
*
* @param  string params - holds the request.POST form data.
* @param  string merchant_key - holds the merchant key.
* @param  string salt - holds the merchant salt key.
* @param  string env - holds the env(enviroment)
*
* @return array result - holds the payment link and status.
*
'''
def initiate_payment(params, merchant_key, salt, env):
    try:
        result = _payment(params, merchant_key, salt, env)
        return _paymentResponse(result)

    except Exception as e:
        traceback.print_exc()
        print("#######Error on payment:initiate_payment#######")
        return ({"status": False, "reason": 'Exception occured'});


'''
* _payment method use for initiate payment.
*
* param string key - holds the merchant key.
* param string txnid - holds the transaction id.
* param string firstname - holds the first name.
* param string email - holds the email.
* param string amount - holds the amount.
* param string phone - holds the phone.
* param string hash - holds the hash key.
* param string productInfo - holds the product information.
* param string successURL - holds the success URL.
* param string failureURL - holds the failure URL.
* param string udf1 - holds the udf1.
* param string udf2 - holds the udf2.
* param string udf3 - holds the udf3.
* param string udf4 - holds the udf4.
* param string udf5 - holds the udf5.
* param string address1 - holds the first address.
* param string address2 - holds the second address.
* param string city - holds the city.
* param string state - holds the state.
* param string country - holds the country.
* param string zipcode - holds the zipcode.
*
* #### Define variable
*
* postedArray array - holds merchant key and request.POST form data.
* URL        string - holds url based on the env(enviroment : 'test' or 'prod')
*
* ##Return values
*
* - return array pay_result - holds the response with status and data.
*
* - return integer status = 1 successful.
*
* - return integer status = 0 error.
*
* @param  string key - holds the merchant key.
* @param  string txnid - holds the transaction id.
* @param  string firstname - holds the first name.
* @param  string email - holds the email.
* @param  string amount - holds the amount.
* @param  string phone - holds the phone.
* @param  string hash - holds the hash key.
* @param  string productInfo - holds the product information.
* @param  string successURL - holds the success URL.
* @param  string failureURL - holds the failure URL.
* @param  string udf1 - holds the udf1.
* @param  string udf2 - holds the udf2.
* @param  string udf3 - holds the udf3.
* @param  string udf4 - holds the udf4.
* @param  string udf5 - holds the udf5.
* @param  string address1 - holds the first address.
* @param  string address2 - holds the second address.
* @param  string city - holds the city.
* @param  string state - holds the state.
* @param  string country - holds the country.
* @param  string zipcode - holds the zipcode.
*
* @return array pay_result - holds the response with status and data.
* @return integer status = 1 successful.
* @return integer status = 0 error.
*
* Note => type() method use for check which types of value holds by variable.
'''
def _payment(params, merchant_key, salt, env):

    postedArray = {}
    URL = None

    # argument validation
    argument_validation = _checkArgumentValidation(params, merchant_key, salt, env)
    if type(argument_validation) == type({}) and argument_validation['status'] == 0:
        return argument_validation

    # push merchant key into params dictionary.
    # params._mutable = True
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

    # process to start pay
    pay_result = _pay(postedArray, salt, URL)

    return pay_result


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
      'firstname' : params['firstname'].strip(),
      'email' : params['email'].strip(),
      'phone' : params['phone'].strip(),
      'udf1' : params['udf1'].strip(),
      'udf2' : params['udf2'].strip(),
      'udf3' : params['udf3'].strip(),
      'udf4' : params['udf4'].strip(),
      'udf5' : params['udf5'].strip(),
      'productinfo' :params['productinfo'].strip(),
      'surl' : params['surl'].strip(),
      'furl' : params['furl'].strip(),
      'address1' : params['address1'].strip(),
      'address2' : params['address2'].strip(),
      'city' : params['city'].strip(),
      'state' : params['state'].strip(),
      'country' : params['country'].strip(),
      'zipcode' : params['zipcode'].strip()
    }
    return temp_distionary


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

    if not(isinstance(params['amount'], float)):
        type_value = "The amount should float up to two or one decimal."

    if not(isinstance(params['productinfo'], str)):
        type_value =  "Product Information should be string"

    if not(isinstance(params['firstname'], str)):
        type_value =  "First Name should be string"

    if not(isinstance(params['phone'], str)):
        type_value = "Phone Number should be number"

    if not(isinstance(params['email'], str)):
        type_value = "Email should be string"

    if not(isinstance(params['surl'], str)):
        type_value = "Success URL should be string"

    if not(isinstance(params['furl'], str)):
        type_value = "Failure URL should be string"

    if type_value != False:
        return {
           'status' : 0,
            'data' : type_value
        }

    return True


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
        empty_value = 'Amount'

    if not params['firstname']:
        empty_value = 'First Name'

    if not params['email']:
        empty_value ='Email'

    if not params['phone']:
        empty_value = 'Phone'

    if not params['productinfo']:
        empty_value ='Product Infomation'

    if not params['surl']:
        empty_value ='Success URL'

    if not params['furl']:
        empty_value ='Failure URL'

    if not salt:
        empty_value = 'Merchant Salt Key'

    if empty_value != False:
        return {
            'status' : 0,
            'data' : 'Mandatory Parameter '+ empty_value +' can not empty'
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
        url_link = "https://testpay.easebuzz.in/"
    elif env == 'prod':
        url_link = 'https://pay.easebuzz.in/'
    elif env == 'dev':
        url_link = 'https://devpay.easebuzz.in/'
    else:
        url_link = "https://testpay.easebuzz.in/"

    return url_link


'''
* _pay method initiate payment will be start from here.
*
* params array params_array - holds all form data with merchant key, transaction id etc.
* params string salt_key - holds the merchant salt key.
* params string url - holds the url based in env(enviroment type env = 'test' or env = 'prod')
*
* param  string key - holds the merchant key.
* param  string txnid - holds the transaction id.
* param  string firstname - holds the first name.
* param  string email - holds the email.
* param  float amount - holds the amount.
* param  string phone - holds the phone.
* param  string hash - holds the hash key.
* param  string productInfo - holds the product information.
* param  string successURL - holds the success URL.
* param  string failureURL - holds the failure URL.
* param  string udf1 - holds the udf1.
* param  string udf2 - holds the udf2.
* param  string udf3 - holds the udf3.
* param  string udf4 - holds the udf4.
* param  string udf5 - holds the udf5.
* param  string address1 - holds the first address.
* param  string address2 - holds the second address.
* param  string city - holds the city.
* param  string state - holds the state.
* param  string country - holds the country.
* param  string zipcode - holds the zipcode.
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
* @param  string firstname - holds the first name.
* @param  string email - holds the email.
* @param  float amount - holds the amount.
* @param  string phone - holds the phone.
* @param  string hash - holds the hash key.
* @param  string productInfo - holds the product information.
* @param  string successURL - holds the success URL.
* @param  string failureURL - holds the failure URL.
* @param  string udf1 - holds the udf1.
* @param  string udf2 - holds the udf2.
* @param  string udf3 - holds the udf3.
* @param  string udf4 - holds the udf4.
* @param  string udf5 - holds the udf5.
* @param  string address1 - holds the first address.
* @param  string address2 - holds the second address.
* @param  string city - holds the city.
* @param  string state - holds the state.
* @param  string country - holds the country.
* @param  string zipcode - holds the zipcode.
*
* @return array with status and data - holds the details
* @return integer status = 0 means error.
* @return integer status = 1 means success and go the url link.
*
'''
def _pay(params_array, salt_key, url):
    hash_key = None

    # generate hash key and push into params array.
    hash_key = _getHashKey(params_array, salt_key)

    params_array['hash'] = hash_key

    # requests call for initiate pay link
    request_result = requests.post(url + 'payment/initiateLink', params_array)

    result = json.loads(request_result.content)

    if result['status'] == 1:
        accesskey = result['data']
    else:
        accesskey = ""

    if not accesskey:
        return result
    else:
        return {
            'status' : 1,
            'data' : url + 'pay/' + accesskey,
            'access_key': accesskey
        }


'''
* _getHashKey method generate Hash key based on the API call (initiatePayment API).
*
* hash formate (hash sequence) :
*  hash = key|txnid|amount|productinfo|firstname|email|udf1|udf2|udf3|udf4|udf5|udf6|udf7|udf8|udf9|udf10|salt
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
    hash_sequence = "key|txnid|amount|productinfo|firstname|email|udf1|udf2|udf3|udf4|udf5|udf6|udf7|udf8|udf9|udf10"
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
* _paymentResponse method show response after API call.
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
def _paymentResponse(params_array):

    if params_array['status'] == 1:

        return {
            "status" : 1,
            "data" : params_array['data'], #.encode('utf-8')
            "access_key" : params_array['access_key']
        }
    else:
        return params_array


'''
* easebuzzResponse method verify API response is acceptable or not and returns the response object.
*
* params array response_params - holds the response array.
* params string salt - holds the merchant salt key.
*
* ##Return values
*
* - return array with status and data - holds the details.
*
* - return integer status = 0 means error.
*
* - return integer status = 1 means success.
*
* @params array response_params - holds the response array.
* @params string salt - holds the merchant salt key.
*
* @return array with status and data - holds the details.
* @return integer status = 0 means error.
* @return integer status = 1 means success.
*
'''
def easebuzzResponse(response_params, salt_key):

    if len(response_params) == 0:
        return {
            'status' : 0,
            'data' : 'Response params is empty.'
        }

    # remove white space, htmlentities, prepared easebuzzPaymentResponse.
    easebuzzPaymentResponse = _removeSpaceAndPrepareAPIResponseArray(response_params)

    # empty validation
    empty_validation = _emptyValidation(easebuzzPaymentResponse, salt_key)
    if empty_validation != True:
        return empty_validation

    # check response the correct or not
    response_result = _getResponse(easebuzzPaymentResponse, salt_key)

    return response_result


'''
*  _removeSpaceAndPrepareAPIResponseArray method Remove white space, converts characters to HTML entities
*   and prepared the posted array.
*
* param array response_array - holds the API response array.
*
* ##Return values
*
* - return array temp_array - holds the all posted value after removing space.
*
* @param array response_array - holds the API response array.
*
* @return array temp_array - holds the all posted value after removing space.
*
'''
def _removeSpaceAndPrepareAPIResponseArray(response_array):
    temp_dictionary = {}
    for key in response_array:
        # for python 2
        # temp_dictionary[key.encode('utf-8')] = str(response_array[key]).strip()

        # for python 3
        temp_dictionary[key] = str(response_array[key]).strip()
    return temp_dictionary


'''
* _getResponse check response is correct or not.
*
* param array response_array - holds the API response array.
* param array s_key - holds the merchant salt key
*
* ##Return values
*
* - return array with status and data - holds the details.
*
* - return integer status = 0 means error.
*
* - return integer status = 1 means success.
*
* @param array response_array - holds the API response array.
* @param array s_key - holds the merchant salt key
*
* @return array with status and data - holds the details.
* @return integer status = 0 means error.
* @return integer status = 1 means success.
*
'''
def _getResponse(response_array, s_key):

    # reverse hash key for validation means response is correct or not.
    reverse_hash_key = _getReverseHashKey(response_array, s_key)

    if reverse_hash_key == response_array['hash']:

        if response_array['status'] == 'success':
            return {
                'status' : 1,
                'url' : response_array['surl'],
                'data' : response_array
            }
        elif response_array['status'] == 'failure':
            return {
                'status' : 1,
                'url' : response_array['furl'],
                'data' : response_array
            }
        else:
            return {
                'status' : 1,
                'data' : response_array
            }
    else:
        return {
            'status' : 0,
            'data' : 'Hash key Mismatch'
        }


'''
* _getReverseHashKey to generate Reverse hash key for validation
*
* reverse hash formate (hash sequence) :
*  reverse_hash = salt|response_array['status']|udf10|udf9|udf8|udf7|udf6|udf5|udf4|udf3|udf2|udf1|email|   *                   firstname|productinfo|amount|txnid|key
*
* params string reverse_hash_sequence - holds the formate of reverse hash key (sequence).
* params array response_array - holds the response array.
* params string s_key - holds the merchant salt key.
*
* ##Return values
*
* - return string  reverse_hash - holds the generated reverse hash key.
*
* @params string reverse_hash_sequence - holds the formate of reverse hash key (sequence).
* @params array response_array - holds the response array.
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
    reverse_hash_string += s_key + '|' + response_array['status']

    for value in hash_sequence_array:
        reverse_hash_string += "|"
        if value in response_array:
            reverse_hash_string += str(response_array[value])
        else:
            reverse_hash_string += ""

    return  sha512(reverse_hash_string.encode('utf-8')).hexdigest().lower()


