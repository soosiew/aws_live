from flask import Flask, render_template, request
from pymysql import connections
import os
import boto3
from config import *

app = Flask(__name__)

bucket = custombucket
region = customregion

db_conn = connections.Connection(
    host=customhost,
    port=3306,
    user=customuser,
    password=custompass,
    db=customdb

)
output = {}
table = 'employee'

@app.route('/')
def index():
    return render_template('home.html', number=1)

@app.route('/register_company')
def register_company():
    return render_template('RegisterCompany.html')

@app.route('/login_company')
def login_company():
    return render_template('LoginCompany.html')

@app.route('/manage_company_profile')
def manage_company_profile():
    return render_template('EditCompanyProfile.html')

@app.route('/login_admin')
def login_admin():
    return render_template('LoginAdmin.html')

@app.route("/addCompanyReg", methods=['POST'])
def addCompanyRegistration():
    try:
        # Create a cursor
        cursor = db_conn.cursor()
        
        # Execute the SELECT COUNT(*) query to get the total row count
        select_sql = "SELECT COUNT(*) as total FROM company"      
        cursor.execute(select_sql)
        result = cursor.fetchone()
        print(result)
        
        # Get the total row count from the result
        total_count = result['total']
        print("total in company - " + total_count)
        
        # Close the cursor
        cursor.close()

        company_id = total_count
        company_name = request.form['company_name']
        company_image_file = request.files['company_image_file']
        about_company = request.form['about_company']
        company_phone = request.form['company_phone']
        company_address = request.form['company_address']
        company_email = request.form['company_email']
        password = request.form['password']

        insert_sql = "INSERT INTO company VALUES (%d, %s, %s, %s, %s, %s, %s, %s)"
        cursor = db_conn.cursor()

        if company_image_file.filename == "":
            return "Please select a file"
        
        try:
                cursor.execute(insert_sql, (company_id, password, company_name, about_company, company_address, company_email, company_phone, ""))
                db_conn.commit()
                
                # Uplaod image file in S3 #
                comp_image_file_name_in_s3 = "comp-id-" + str(company_id) + "_image_file"
                s3 = boto3.resource('s3')

                try:
                    print("Data inserted in MySQL RDS... uploading image to S3...")
                    s3.Bucket(custombucket).put_object(Key=comp_image_file_name_in_s3, Body=company_image_file)
                    bucket_location = boto3.client('s3').get_bucket_location(Bucket=custombucket)
                    s3_location = (bucket_location['LocationConstraint'])

                    if s3_location is None:
                        s3_location = ''
                    else:
                        s3_location = '-' + s3_location

                    object_url = "https://s3{0}.amazonaws.com/{1}/{2}".format(
                        s3_location,
                        custombucket,
                        comp_image_file_name_in_s3)

                except Exception as e:
                    return str(e)
        
        finally:
            cursor.close()

        print("Company registration request submitted...")
        return render_template('EditCompanyProfile.html')
    
    except Exception as e:
        print(str(e))
        print("failed get count...")
        return render_template('home.html')













@app.route("/", methods=['GET', 'POST'])
def home():
    return render_template('AddEmp.html')

@app.route("/about", methods=['POST'])
def about():
    return render_template('www.tarc.edu.my')

@app.route("/addemp", methods=['POST'])
def AddEmp():
    emp_id = request.form['emp_id']
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    pri_skill = request.form['pri_skill']
    location = request.form['location']
    emp_image_file = request.files['emp_image_file']

    insert_sql = "INSERT INTO employee VALUES (%s, %s, %s, %s, %s)"
    cursor = db_conn.cursor()

    if emp_image_file.filename == "":
        return "Please select a file"

    try:

        cursor.execute(insert_sql, (emp_id, first_name, last_name, pri_skill, location))
        db_conn.commit()
        emp_name = "" + first_name + " " + last_name
        # Uplaod image file in S3 #
        emp_image_file_name_in_s3 = "emp-id-" + str(emp_id) + "_image_file"
        s3 = boto3.resource('s3')

        try:
            print("Data inserted in MySQL RDS... uploading image to S3...")
            s3.Bucket(custombucket).put_object(Key=emp_image_file_name_in_s3, Body=emp_image_file)
            bucket_location = boto3.client('s3').get_bucket_location(Bucket=custombucket)
            s3_location = (bucket_location['LocationConstraint'])

            if s3_location is None:
                s3_location = ''
            else:
                s3_location = '-' + s3_location

            object_url = "https://s3{0}.amazonaws.com/{1}/{2}".format(
                s3_location,
                custombucket,
                emp_image_file_name_in_s3)

        except Exception as e:
            return str(e)

    finally:
        cursor.close()

    print("all modification done...")
    return render_template('AddEmpOutput.html', name=emp_name)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)

