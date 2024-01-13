from flask import Flask, render_template, request, redirect, url_for, session, send_file
from flask_mysqldb import MySQL
from werkzeug.utils import secure_filename
import MySQLdb.cursors
from passlib.hash import sha256_crypt
import re
import os
from datetime import datetime
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas


app = Flask(__name__)

app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "scc"
app.config["UPLOAD_FOLDER"] = "F:\imcc study material\SEM - 3\SCC\SCC\static\profilepic"
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024
app.config["SECRET_KEY"] = "secret_key"
mysql = MySQL(app)


@app.route("/", methods=["GET", "POST"])
def homepage():
    return render_template("index.html")


@app.route("/contact", methods=["GET", "POST"])
def contact():
    return render_template("contact.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if "email" in session:
        return redirect("/dashboard")
    else:
        return render_template("login.html")


@app.route("/about", methods=["GET", "POST"])
def about():
    return render_template("about.html")


@app.route("/jaKabutarja", methods=["GET", "POST"])
def jaKabutarja():
    sno = "NULL"
    roll = session["roll"]
    cname = request.form["CourseId"]
    cid = request.form["Cid"]
    cbatch = request.form["Batch"]
    cteacher = request.form["Teacher"]
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute(
        "INSERT INTO registered_courses VALUES (% s, % s, % s, % s, % s, % s)",
        (
            sno,
            roll,
            cname,
            cid,
            cbatch,
            cteacher,
        ),
    )
    mysql.connection.commit()

    return redirect("/dashboard")


@app.route("/cregister", methods=["GET", "POST"])
def cregister():
    if "email" in session:
        course_id = request.form["CourseId"]
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM all_courses WHERE Cid = % s", (course_id,))
        details = cursor.fetchone()
        return render_template("cregister.html", details=details)

    else:
        return render_template("login.html")


@app.route("/courses", methods=["GET", "POST"])
def courses():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM all_courses")
    results = cursor.fetchall()

    # for row in results:
    #     print("Testing: ", row['Course'])

    return render_template("courses.html", results=results)


@app.route("/register", methods=["GET", "POST"])
def register():
    msg = ""

    if request.method == "POST" and "Name" in request.form and "Email" in request.form:
        Rollno = "NULL"
        Name = request.form["Name"]
        Age = request.form["Age"]
        Gender = request.form["Gender"]
        Email = request.form["Email"]
        Mobile = request.form["Mobile"]
        Address = request.form["Address"]
        Password = request.form["Password"]
        enc_pwd = sha256_crypt.encrypt(Password)
        file = request.files["Photo"]
        file.save(
            os.path.join(app.config["UPLOAD_FOLDER"], secure_filename(file.filename))
        )
        Photo = request.files["Photo"].filename

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM studentreg WHERE Email = % s", (Email,))
        account = cursor.fetchone()
        if account:
            msg = "Account already exists !"
        elif not re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", Email):
            msg = "Invalid email address !"
        elif not re.match(r"^(0|91)?[6-9][0-9]{9}", Mobile):
            msg = "Invalid Mobile number !"
        elif not re.match(
            r"^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,}$", Password
        ):
            msg = "Invalid Password !"
        else:
            cursor.execute(
                "INSERT INTO studentreg VALUES (% s, % s, % s, % s, % s, % s, % s, % s, % s)",
                (
                    Rollno,
                    Name,
                    Age,
                    Gender,
                    Email,
                    Mobile,
                    Address,
                    Photo,
                    enc_pwd,
                ),
            )
            mysql.connection.commit()
            return redirect(url_for("login"))
    elif request.method == "POST":
        msg = "Please fill out the form !"
    return render_template("register.html", msg=msg)


# Student Login and logout
@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    msg = ""
    results = None
    if "email" in session:
        return render_template("dashboard.html", msg=msg)
    if (
        request.method == "POST"
        and "Email" in request.form
        and "Password" in request.form
    ):
        Email = request.form["Email"]
        Password = request.form["Password"]

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM studentreg WHERE Email = % s", (Email,))
        pwd = cursor.fetchone()
        db_pwd = pwd["Password"]
        profilepic = pwd["Photo"]

        # fetch data from db for all_courses table
        cursor.execute("SELECT * FROM all_courses")
        results = cursor.fetchall()

        # fetch data from db for upcoming courses table
        cursor.execute("SELECT * FROM upcoming_courses")
        uc = cursor.fetchall()

        if db_pwd and sha256_crypt.verify(Password, db_pwd):
            if sha256_crypt.verify(Password, db_pwd):
                session["loggedin"] = True
                session["roll"] = pwd["Rollno"]
                session["name"] = pwd["Name"]
                session["age"] = pwd["Age"]
                session["gender"] = pwd["Gender"]
                session["email"] = pwd["Email"]
                session["contact"] = pwd["Contact"]
                session["address"] = pwd["Address"]

                session["profilepic"] = profilepic

                # fetch data from db for upcoming courses
                Rollno = pwd["Rollno"]
                cursor.execute(
                    "SELECT * FROM registered_courses WHERE Rollno = %s", (Rollno,)
                )
                reg = cursor.fetchall()

                return render_template(
                    "dashboard.html", msg=msg, results=results, uc=uc, reg=reg
                )
        else:
            msg = "Please enter correct email / password !"
    return render_template("login.html", msg=msg)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("courses"))


@app.route("/contactus", methods=["GET", "POST"])
def contact_us():
    if request.method.upper() == "POST":
        Name = request.form["name"]
        Age = request.form["email"]
        Gender = request.form["message"]
        current_date = datetime.now()
        Date = current_date.strftime("%d %m %Y")

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        query = "INSERT INTO query VALUES (%s,%s,%s,%s)"
        cursor.execute(
            query,
            (Name, Age, Gender, Date),
        )
        mysql.connection.commit()
        return render_template("contact.html")


@app.route("/view_query")
def view_query():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    query = "SELECT * FROM query"
    cursor.execute(query)
    contacted_msg = cursor.fetchall()
    mysql.connection.commit()
    # print(contacted_msg)
    return render_template("display_query.html", contacted_msg=contacted_msg)


@app.route("/admin")
def admin():
    return render_template("admin_login.html")


@app.route("/admin_dashbord", methods=["POST"])
def admin_dashbord():
    if request.method.upper() == "POST":
        username = request.form["adminName"]
        password = request.form["adminPassword"]
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        cursor.execute("SELECT * FROM admin WHERE admin_name=%s", (username,))
        admin = cursor.fetchone()
        if admin and admin["password"] == password:
            return render_template("admin_dashbord.html")
        else:
            return render_template("admin_login.html")
    return render_template("admin_login.html")


@app.route("/admin_addcourse", methods=["GET", "POST"])
def admin_addcourse():
    if request.method.upper() == "POST":
        Cid = request.form["courseID"]
        Course = request.form["courseName"]
        Batch = request.form["timing"]
        Teacher = request.form["teacherName"]
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        Sno = ""
        query = (
            "INSERT INTO all_courses (Cid, Course, Batch, Teacher) VALUES (%s,%s,%s,%s)"
        )
        cursor.execute(
            query,
            (Cid, Course, Batch, Teacher),
        )
        mysql.connection.commit()
        cursor.close()

    return render_template("admin_dashbord.html")


@app.route("/view_course")
def admin_course():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM all_courses")
    results = cursor.fetchall()
    return render_template("admin_course.html", results=results)


@app.route("/c_remove", methods=["GET", "POST"])
def c_remove():
    if request.method == "POST":
        Cid = request.form["CourseId"]
        try:
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            query = "DELETE FROM all_courses WHERE Cid = %s"
            cursor.execute(query, (Cid,))
            mysql.connection.commit()
        except Exception as e:
            print("An error occurred:", str(e))
        finally:
            cursor.close()

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM all_courses")
    results = cursor.fetchall()

    return render_template("admin_course.html", results=results)


@app.route("/generate_pdf")
def genrate_and_download_report():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT Cid, Course, student_name, Rollno FROM registered_courses")
    result = cursor.fetchall()
    mysql.connection.commit()

    count_dict = {}

    # Create a PDF buffer
    pdf_buffer = BytesIO()

    # Create a PDF file
    c = canvas.Canvas(pdf_buffer, pagesize=letter)

    # Define the PDF content
    c.setFont("Helvetica", 12)

    # Add the header section with the name, logo, and date
    c.setFillColor(colors.cadetblue)
    c.setFont("Helvetica-Bold", 20)  # Set the font style to bold
    c.drawString(200, 770, "SUNSHINE COACHING")

    c.setFillColor(colors.black)
    c.setFont("Helvetica", 12)

    c.drawImage(
        "logo.jpeg", 470, 780, width=70, height=-30
    )  # Replace "path_to_logo.png" with the actual logo path
    c.drawString(50, 735, "Course Enrollment Report")
    current_date = datetime.now()
    Date = current_date.strftime("%d %m %Y")
    c.drawString(470, 735, Date)  # Replace with the actual date

    # Draw a line to separate the header
    c.line(50, 730, 550, 730)

    header = ["Cid", "Course", "Student Name", "Rollno"]

    x_start = 50
    y_start = 700
    x_offset = 150
    y_offset = 30

    # Draw headers
    for i, header_item in enumerate(header):
        c.drawString(x_start + (i * x_offset), y_start, header_item)

    # Iterate through the data
    for i, data_row in enumerate(result):
        y_start -= y_offset
        c.drawString(x_start, y_start, data_row["Cid"])
        c.drawString(x_start + x_offset, y_start, data_row["Course"])
        c.drawString(x_start + 2 * x_offset, y_start, data_row["student_name"])
        c.drawString(x_start + 3 * x_offset, y_start, str(data_row["Rollno"]))

        # Update count for the Cid in the dictionary
        count_dict[data_row["Cid"]] = count_dict.get(data_row["Cid"], 0) + 1

    # Draw the counts
    y_start -= 2 * y_offset
    c.drawString(x_start, y_start, "Total Count for each Cid:")
    for cid, count in count_dict.items():
        y_start -= y_offset
        c.drawString(x_start, y_start, f"{cid}: {count}")

    # Save the PDF
    c.showPage()
    c.save()

    pdf_buffer.seek(0)

    # Return the PDF file for download
    return send_file(pdf_buffer, as_attachment=True, download_name="course_report.pdf")

    # return render_template("base.html")


if __name__ == "__main__":
    app.run(debug=True)
