from flask import Flask, render_template, request, session, Response
from pymysql import connections
import os
import boto3
import datetime
import base64
from config import *

app = Flask(__name__)
app.secret_key = "CC"

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

@app.route('/logoutCompany')
def logoutCompany():  
    if 'id' in session:  
        session.pop('logedInCompany',None)  
        return render_template('home.html');  
    else:  
        return render_template('home.html'); 

@app.route('/logoutAdmin')
def logoutAdmin():  
    if 'id' in session:  
        session.pop('logedInAdmin',None)  
        return render_template('home.html');  
    else:  
        return render_template('home.html');

@app.route('/register_company')
def register_company():
    return render_template('RegisterCompany.html')

@app.route('/publish_job')
def publish_job():
    return render_template('PublishJob.html')

@app.route('/companyViewApplication')
def companyViewApplication():
    return render_template('ViewCompanyApplication.html')

@app.route('/companyViewManageJob')
def companyViewManageJob():
    return render_template('CompanyViewManageJob.html')

@app.route('/login_company')
def login_company():
    return render_template('LoginCompany.html')

@app.route('/updateCompanyPassword', methods=['POST'])
def updateCompanyPassword():
    currentCompany = str(session['logedInCompany'])
    password = request.form['new_password']
    
    update_sql = "UPDATE company SET password=%s WHERE companyId=%s"
    cursor = db_conn.cursor()

    try:
        # Check if the company exists
        check_sql = "SELECT * FROM company WHERE companyId = %s"
        cursor.execute(check_sql, (currentCompany,))
        existing_company = cursor.fetchone()

        if not existing_company:
            return "Company not found"
        
        cursor.execute(update_sql, (password, int(currentCompany)))
        db_conn.commit()

    finally:
        cursor.close()
        print("Company password updated successfully...")
        
        # Reload page with updated company profile
        currentCompany = str(session['logedInCompany'])
        select_sql = "SELECT * FROM company WHERE companyId = %s"
        cursor = db_conn.cursor()

        try:
            cursor.execute(select_sql, (currentCompany,))
            company = cursor.fetchone()

            if not company:
                print("company not found")

            comp_name = company[2]
            comp_about = company[3]
            comp_address = company[4]
            comp_email = company[5]
            comp_phone = company[6]

            # Fetch the S3 image URL based on comp_id
            comp_image_file_name_in_s3 = "comp-id-" + str(currentCompany) + "_image_file"
            s3 = boto3.client('s3')
            bucket_name = custombucket

            try:
                response = s3.generate_presigned_url('get_object',
                                                    Params={'Bucket': bucket_name,
                                                            'Key': comp_image_file_name_in_s3},
                                                    ExpiresIn=7400)  # Adjust the expiration time as needed            
                return render_template('EditCompanyProfile.html', name=comp_name, compName=comp_name, compLogo=response, compAbout=comp_about, compAddress=comp_address, compEmail=comp_email, compPhone=comp_phone)
                
            except Exception as e:
                print(str(e))

        except Exception as e:
            print(str(e))

        finally:
            cursor.close()

@app.route("/updateCompanyProfile", methods=['POST'])
def updateCompanyProfile():
    currentCompany = str(session['logedInCompany'])
    companyName = request.form['company_name']
    companyAbout = request.form['about_company']
    companyPhone = request.form['company_phone']
    companyEmail = request.form['company_email']
    companyAddress = request.form['company_address']
    company_image_file = request.files['company_image_file']

    update_sql = "UPDATE company SET name=%s, about=%s, phone=%s, email=%s, address=%s WHERE companyId=%s"
    cursor = db_conn.cursor()
    
    try:
        # Check if the company exists
        check_sql = "SELECT * FROM company WHERE companyId = %s"
        cursor.execute(check_sql, (currentCompany,))
        existing_company = cursor.fetchone()

        if not existing_company:
            return "Company not found"
        
        cursor.execute(update_sql, (companyName, companyAbout, companyPhone, companyEmail, companyAddress, int(currentCompany)))
        db_conn.commit()
        
        if company_image_file.filename != "" : 
            # Update image file in S3
            comp_image_file_name_in_s3 = "comp-id-" + str(currentCompany) + "_image_file"
            s3 = boto3.resource('s3')

            try:
                print("Updating company profile...")
                s3.Bucket(custombucket).put_object(Key=comp_image_file_name_in_s3, Body=company_image_file)
                bucket_location = boto3.client('s3').get_bucket_location(Bucket=custombucket)
                s3_location = (bucket_location.get('LocationConstraint'))

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
        print("Company profile updated successfully...")
        
        # Reload page with updated company profile
        currentCompany = str(session['logedInCompany'])
        select_sql = "SELECT * FROM company WHERE companyId = %s"
        cursor = db_conn.cursor()

        try:
            cursor.execute(select_sql, (currentCompany,))
            company = cursor.fetchone()

            if not company:
                print("company not found")

            comp_name = company[2]
            comp_about = company[3]
            comp_address = company[4]
            comp_email = company[5]
            comp_phone = company[6] 

            # Fetch the S3 image URL based on comp_id
            comp_image_file_name_in_s3 = "comp-id-" + str(currentCompany) + "_image_file"
            s3 = boto3.client('s3')
            bucket_name = custombucket

            try:
                response = s3.generate_presigned_url('get_object',
                                                    Params={'Bucket': bucket_name,
                                                            'Key': comp_image_file_name_in_s3},
                                                    ExpiresIn=7400)  # Adjust the expiration time as needed            
                return render_template('EditCompanyProfile.html', name=comp_name, compName=comp_name, compLogo=response, compAbout=comp_about, compAddress=comp_address, compEmail=comp_email, compPhone=comp_phone)
                
            except Exception as e:
                print(str(e))

        except Exception as e:
            print(str(e))

        finally:
            cursor.close()
        

@app.route('/manage_company_profile')
def manage_company_profile():
    currentCompany = str(session['logedInCompany'])
    select_sql = "SELECT * FROM company WHERE companyId = %s"
    cursor = db_conn.cursor()

    try:
        cursor.execute(select_sql, (currentCompany,))
        company = cursor.fetchone()

        if not company:
            print("company not found")

        comp_name = company[2]
        comp_about = company[3]
        comp_address = company[4]
        comp_email = company[5]
        comp_phone = company[6] 

        # Fetch the S3 image URL based on comp_id
        comp_image_file_name_in_s3 = "comp-id-" + str(currentCompany) + "_image_file"
        s3 = boto3.client('s3')
        bucket_name = custombucket

        try:
            response = s3.generate_presigned_url('get_object',
                                                 Params={'Bucket': bucket_name,
                                                         'Key': comp_image_file_name_in_s3},
                                                 ExpiresIn=7400)  # Adjust the expiration time as needed            
            return render_template('EditCompanyProfile.html', name=comp_name, compName=comp_name, compLogo=response, compAbout=comp_about, compAddress=comp_address, compEmail=comp_email, compPhone=comp_phone)
            
        except Exception as e:
            print(str(e))

    except Exception as e:
        print(str(e))

    finally:
        cursor.close()
        

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
        
        cursor.close()

        company_id = int(result[0]) + 1
        company_name = request.form['company_name']
        company_image_file = request.files['company_image_file']
        about_company = request.form['about_company']
        company_phone = request.form['company_phone']
        company_address = request.form['company_address']
        company_email = request.form['company_email']
        password = request.form['password']

        insert_sql = "INSERT INTO company VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
        cursor = db_conn.cursor()

        if company_image_file.filename == "":
            return "Please select a file"
        
        try:
                cursor.execute(insert_sql, (company_id, password, company_name, about_company, company_address, company_email, company_phone, "pending",))
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
            return render_template('home.html')
    
    except Exception as e:
        print(str(e))
        print("failed get count...")
        return render_template('home.html')
    
@app.route("/addJob", methods=['POST'])
def addJob():
    try:
        # Create a cursor
        cursor = db_conn.cursor()
        
        # Execute the SELECT COUNT(*) query to get the total row count
        select_sql = "SELECT COUNT(*) as total FROM job"      
        cursor.execute(select_sql)
        result = cursor.fetchone()
        
        cursor.close()
        current_datetime = datetime.datetime.now()

        # Format the date as a string (e.g., "2023-09-09 10:15:30")
        job_id = int(result[0]) + 1
        publish_date = current_datetime.strftime('%Y-%m-%d %H:%M:%S')       
        job_type = request.form['job_type']
        job_position = request.form['job_position']
        job_description = request.form['job_description']
        job_requirement = request.form['job_requirement']
        job_location = request.form['job_location']
        job_salary = request.form['job_salary']
        job_openings = request.form['job_openings']       
        job_industry = request.form['job_industry']
        company = int(session['logedInCompany'])

        insert_sql = "INSERT INTO job VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        cursor = db_conn.cursor()

        try:
            cursor.execute(insert_sql, (job_id, publish_date, job_type, job_position, job_description, job_requirement, job_location, job_salary, job_openings, company, job_industry,))
            db_conn.commit()
               
        except Exception as e:
                print(str(e))

    except Exception as e:
                print(str(e))

    finally:
        cursor.close()
        print("Job published...")
        return render_template('ViewCompanyApplication.html')
    


@app.route("/loginCompany", methods=['GET','POST'])
def loginCompany():
    if request.method == 'POST':
        email = request.form['company_email']
        password = request.form['password']

        select_sql = "SELECT * FROM company WHERE email = %s AND password = %s"
        cursor = db_conn.cursor()

        try:
            cursor.execute(select_sql, (email,password,))
            company = cursor.fetchone()

            if company:  
                session['logedInCompany'] = str(company[0])
                return render_template('ViewCompanyApplication.html', id = session['logedInCompany'], name = company[2])
            
        except Exception as e:
            return str(e)
        
        finally:   
            cursor.close()
        
    return render_template('LoginCompany.html', msg="Access Denied : Invalid email or password")

@app.route("/loginAdmin", methods=['GET','POST'])
def loginAdmin():
    if request.method == 'POST':
        admin_id = request.form['admin_ID']
        password = request.form['password']

        if admin_id != "Admin001" or password != "12345678":
            return render_template('LoginAdmin.html')
        session['logedInAdmin'] = str(admin_id)
        return render_template('AdminDashboard.html', id=session['logedInAdmin'])














































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

