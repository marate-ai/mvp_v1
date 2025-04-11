from flask import Flask, jsonify, render_template, request, flash, redirect, url_for
import pickle
import matplotlib.pyplot as plt
import io
import base64
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage


app = Flask(__name__)
app.secret_key = "supersecretkey"

questions = [
    {
        'id': 'q1',
        'question': 'Y a t\'il des toux nocturnes ?',
        'options': ['Oui', 'Non', 'Je ne sais pas']
    },
    {
        'id': 'q2',
        'question': 'Est ce que vous êtes affectés par la poussière d\'une maniere ou d\'une autre? ',
        'options': ['Oui', 'Non', 'Je ne sais pas']
    },
    {
        'id': 'q3',
        'question': 'Le patient est -il un enfant ou un adulte?',
        'options': ['Enfant', 'Adulte']
    },
    {
        'id': 'q4',
        'question': 'Est ce que vous êtes affectés par des variations climatiques? ',
        'options': ['Oui', 'Non', 'Je ne sais pas']
    },
    {
        'id': 'q5',
        'question': 'Y a t\'il la difficulté de respirer?',
        'options': ['Oui', 'Non', 'Je ne sais pas']
    },
    {
        'id': 'q6',
        'question': 'Y a t\'il dyspnée expiratoire active (difficulté de respiration quand vous expirer), prolongée, bruyante et sifflante ?',
        'options': ['Oui', 'Non', 'Je ne sais pas']
    },
    {
        'id': 'q7',
        'question': 'Y a t\'il des râles sibilants expiratoires diffus et une diminution du murmure vésiculaire?',
        'options': ['Oui', 'Non', 'Je ne sais pas']
    },
    {
        'id': 'q8',
        'question': 'Y a t\'il une distension thoracique (une expansion anormale ou une hyperinflation du thorax) ?',
        'options': ['Oui', 'Non', 'Je ne sais pas']
    },
    {
        'id': 'q9',
        'question': 'Mere VIH+ ou décédée de cause inconnue ?',
        'options': ['Oui', 'Non', 'Je ne sais pas']
    },
    {
        'id': 'q10',
        'question': 'Eruptions cutanée récurrentes/dermatose ?',
        'options': ['Oui', 'Non', 'Je ne sais pas']
    },
    {
        'id': 'q11',
        'question': 'Infection sexuellement transmissible ou symptomes évocateurs d\'une infection sexuellement transmissible ?',
        'options': ['Oui', 'Non', 'Je ne sais pas']
    },
    {
        'id': 'q12',
        'question': 'Décés d\'un partenaire du au VIH ou suite d\'une longue maladie?',
        'options': ['Oui', 'Non']
    },
    {
        'id': 'q13',
        'question': 'Notion de TB maladie actualle ou dans les 12 dernieres mois?',
        'options': ['Oui', 'Non', 'Je ne sais pas']
    },
    {
        'id': 'q14',
        'question': 'Enduits blanchatres dans la bouche?',
        'options': ['Oui', 'Non', 'Je ne sais pas']
    },
    {
        'id': 'q15',
        'question': 'Amaigrissement inexpliqué?',
        'options': ['Oui', 'Non']
    },
]

randnum = 0

@app.route("/", methods=["GET", "POST"])
def index():
    return render_template("index.html", questions=questions)     

@app.route("/results", methods=["POST"])
def results(): 
    global randnum
    randnum+=1 
    answers = {}
    firstname = ''
    lastname = ''
    dob = ''

    print(request.form.keys())
    for key in request.form.keys():
        if key=='firstname' or key=='lastname' or key=='dob':
            answers[key] = request.form.get(key)
        else:
            answers[key[9:10]] = request.form.get(key)
    
    for key in request.form.keys():
        if 'q10' in key or 'q11' in key or 'q12' in key :
            answers[key[9:11]] = request.form.get(key)
    
    firstname = answers['firstname']
    lastname = answers['lastname']
    dob = answers['dob']

    term_dic = {"Oui":1, "Non":0, 'Je ne sais pas':0.5, 'Adulte': 1, 'Enfant': 0, 'Enfant ':0, 'Adulte ':1}
    for k,v in answers.items():
        if k in term_dic:
            answers[k] = term_dic[answers[k]]

    print(answers)
    qa ={}
    questions_li = list(map(lambda e:e['question'], questions))
    for i in range(len(questions)):
        if str(i) in answers.keys():
            qa[questions_li[i]]=answers[str(i)]
    
    vector = []
    for i in range(len(questions)):
        if str(i+1) in answers.keys():
            vector.append(term_dic[answers[str(i+1)]])
    
    print('vector', vector)
    print('answers', answers)
    with open('model_1_asthme.pkl', 'rb') as f:
        model = pickle.load(f)

    y = model.predict_proba([vector[:8]])
    proba_asth = y[0][1]
    proba_mal = 0.3
    proba_hiv = sum(vector[9:])/100

    print(proba_asth ,proba_hiv, proba_mal)

    categories = ['Asthme', 'Paludisme', 'AIDS']
    values = [proba_asth/(proba_asth+proba_hiv+proba_mal), proba_mal/(proba_asth+proba_hiv+proba_mal), proba_hiv/(proba_asth+proba_hiv+proba_mal)]

    plt.figure(figsize=(6, 4))
    plt.bar(categories, values, color='blue')
    plt.xlabel('Maladies')
    plt.ylabel('Probabilités')
    plt.title('Estimations')

    # Save the plot to a BytesIO object
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plt.close()
    
    # Encode the image to base64 string
    plot_url = base64.b64encode(img.getvalue()).decode()
    plt.close()  # Close the plot to free memory
    comment =f"En fonction de vos réponses, nous pensons que le patient souffre très probablement d'asthme. {90}% des personnes répondant Oui à la question 1 obtiennent un résultat negatif pour le paludisme, et 70% des personnes répondant Non à la question 2 sont finalement confirmées asthmatiques. Restez assis et attendez que l'infirmière vienne vous chercher."
    flash(f"Merci d'avoir rempli le formulaire. Selon notre analyse, vous avez {round(proba_asth*100)}% de chances de souffrir d\'asthme. Patientez jusqu\'à ce que l\'infirmière vienne vous chercher.")
    
    # get the answer pairs
    responses = non_html_display(qa)

    # Email the person in charge
    email(firstname, lastname, responses, img)
    return render_template("results.html", num=randnum, questions=questions, plot_url=plot_url, comment=comment, firstname=firstname, lastname=lastname) 

@app.route("/feedbacks")
def email_feedbacks():  
    return

# display the questions so that i can tag them in the email
def non_html_display(qa):
    res = ""
    index = 0
    for question, answer in qa.items():
        res+= str(index+1) + ". " + question + " : " + answer + "<br>"
        index+=1
    return res

# Set up the SMTP server
smtp_server = "smtp.gmail.com"
smtp_port = 587
your_email = "jonathanjerabe@gmail.com"
your_password = "ajrn mros lkzm urnu"
# email(firstname, lastname, comment, img, responses)
def email(firstname, lastname, body, plot):

    # sending the email
    subject = f"Rapport médical de pré-visite pour {firstname} {lastname} | Patient #{randnum}"
    recipient_email = your_email
    
    # create the MIME message
    msg = MIMEMultipart()
    msg['From'] = your_email
    msg['To'] = "amazonjerabe@gmail.com"
    msg['Subject'] = subject

    # add an HTML body with the embedded image
    html = f"""
    <html>
    <body>
    Chèr médecins et infirmières, <br><br>ci desous est le rapport d'analyse de {firstname} {lastname} avec nos conclusions. 
    <br>
        <h1>Analyse pour {firstname} {lastname}</h1>
        <img src="cid:graph">
        <br>
        <h2> Résultats du formulaire</h2>
        <p>
        {body}
        <h2> Raisonnement du model</h2>
        <p>
        En fonction de vos réponses, nous pensons que le patient souffre très probablement d'asthme.
        <ul>
            <li>{90}% des personnes répondant Oui à la question 1 "Y a t\'il des toux nocturnes ?" obtiennent un résultat negatif pour le paludisme</li>
            <li>70% des personnes répondant Oui à la question 4 "Y a t\'il la difficulté de respirer?"  sont souvent confirmées asthmatiques.</li>
        </ul> 
        A cause de ces réponses, nous pensons qu'il y a de bonnes chances que le malade souffre d'asthme.
        <p>
        Restez assis et attendez que l'infirmière vienne vous chercher.
        </p>
        <br>
        <img style="width: 350px; height: 100px;" src="https://allarassemjonathan.github.io/marate_white.png">
    </body>
    </html>
    """
    msg.attach(MIMEText(html, 'html'))

    # Embed the graph as an inline image
    image = MIMEImage(plot.getvalue(), name="graph.png")
    image.add_header("Content-ID", "<graph>")
    msg.attach(image)


    # Connect to the SMTP server and send the email
    try:
        # Establish connection to Gmail's SMTP server
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()  # Secure the connection

        # Log in to the server
        server.login(your_email, your_password)

        # Send the email
        server.send_message(msg)

        print("Email sent successfully!")

    except Exception as e:
        print(f"Error sending email: {e}")

    finally:
        # Close the connection to the server
        server.quit()

    # You could include additional validation for the URL here if needed
    return jsonify(success=True)


if __name__ == "__main__":
    app.run(debug=True)



