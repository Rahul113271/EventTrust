from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.template import RequestContext
from django.contrib import messages
from django.http import HttpResponse
from django.core.files.storage import FileSystemStorage
import os
import hashlib
from datetime import date
import json
import uuid
import re
from web3 import Web3, HTTPProvider
import pandas as pd
import numpy as np
from string import punctuation
from nltk.corpus import stopwords, wordnet
import nltk
from nltk.stem import WordNetLemmatizer
import pickle
from nltk.stem import PorterStemmer

# Eagerly load WordNet corpus to prevent multithreaded lazy-loading race conditions in Django
try:
    wordnet.ensure_loaded()
except Exception as _e:
    print("WordNet eager load warning:", _e)
import os
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer #loading tfidf vector
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import accuracy_score
from sklearn.metrics import f1_score
from sklearn.metrics import precision_score
from sklearn.metrics import recall_score
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.naive_bayes import GaussianNB
from sklearn import svm
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
import xgboost as xg
import matplotlib.pyplot as plt
from keras.utils import to_categorical
from keras.layers import  MaxPooling2D
from keras.layers import Dense, Dropout, Activation, Flatten, GlobalAveragePooling2D, BatchNormalization, AveragePooling2D
from keras.layers import Convolution2D
from keras.models import Sequential, load_model, Model
import pickle
from keras.callbacks import ModelCheckpoint
import io
import base64

global details, username
details=''
username=''

# Blockchain configuration for local Truffle development network (Network ID: 5777)
BLOCKCHAIN_ADDRESS = 'http://127.0.0.1:9545'
DEPLOYED_CONTRACT_ADDRESS = '0x701c696E418C05CCe7CbcDA51c49B5718B54eada'
COMPILED_CONTRACT_PATH = 'Event.json'

def get_blockchain_contract():
    """Helper to obtain Web3 connection and instantiated Event contract instance."""
    web3 = Web3(HTTPProvider(BLOCKCHAIN_ADDRESS, request_kwargs={'timeout': 60}))
    web3.eth.defaultAccount = web3.eth.accounts[0]
    with open(COMPILED_CONTRACT_PATH) as file:
        contract_json = json.load(file)
        contract_abi = contract_json['abi']
    file.close()
    contract = web3.eth.contract(address=DEPLOYED_CONTRACT_ADDRESS, abi=contract_abi)
    return web3, contract

def calculate_trust_score(verified, confidence, is_disaster):
    """
    Explainable Trust / Reliability Score (0 to 100) for the stored event record:
    
    1. Blockchain Data Integrity (50 Points Max):
       - If verified (Local SHA-256 matches Blockchain-stored Hash): 50 points
       - If tampered / mismatch: 0 points (Hard-Gate: overall trust score drops to 0)
       
    2. Deep Learning Classification Confidence (40 Points Max):
       - Derived directly from actual CNN softmax probability: round((confidence / 100.0) * 40)
       - E.g., 90% confidence -> 36 points; 100% confidence -> 40 points
       
    3. Event Classification Corroboration (10 Points Max):
       - Disaster Event: 10 points (critical event report corroborated by DL classification)
       - Normal Event: 8 points (routine baseline event)
       
    Hard-Gate Rule:
       If data integrity is compromised (tampered record), the trust score is strictly 0.
       Otherwise, Trust Score = min(100, max(0, Integrity (50) + Confidence (max 40) + Event Context (max 10)))
    """
    if not verified:
        return 0
    integrity_pts = 50
    conf_fraction = max(0.0, min(100.0, float(confidence))) / 100.0
    conf_pts = round(conf_fraction * 40.0)
    event_pts = 10 if is_disaster else 8
    total_score = integrity_pts + conf_pts + event_pts
    return max(0, min(100, int(total_score)))



#define object to remove stop words and other text processing
stop_words = set(stopwords.words('english'))
lemmatizer = WordNetLemmatizer()
try:
    lemmatizer.lemmatize('test')
except Exception:
    pass
ps = PorterStemmer()

global accuracy, precision, recall, fscore

accuracy = []
precision = []
recall = []
fscore = []

#define function to clean text by removing stop words and other special symbols
def cleanText(doc):
    tokens = doc.split()
    table = str.maketrans('', '', punctuation)
    tokens = [w.translate(table) for w in tokens]
    tokens = [word for word in tokens if word.isalpha()]
    tokens = [w for w in tokens if not w in stop_words]
    tokens = [word for word in tokens if len(word) > 1]
    tokens = [ps.stem(token) for token in tokens]
    try:
        tokens = [lemmatizer.lemmatize(token) for token in tokens]
    except Exception:
        # Fallback if WordNet lazy loader encountered a multithreaded race condition
        try:
            wordnet.ensure_loaded()
            tokens = [lemmatizer.lemmatize(token) for token in tokens]
        except Exception:
            pass
    tokens = ' '.join(tokens)
    return tokens

#generate SHA-256 hash of post content for blockchain integrity verification
def calculate_post_hash(post_string):
    return hashlib.sha256(post_string.encode("utf-8")).digest()

dataset = pd.read_csv("Dataset/DisasterTweets.csv")
dataset = dataset.dropna()
print(dataset.shape)
dataset = dataset.values
'''
X = []
Y = []

for i in range(len(dataset)):
    tweet = dataset[i,3]
    tweet = tweet.strip("\n").strip().lower()
    label = dataset[i,4]
    tweet = cleanText(tweet)#clean description
    X.append(tweet)
    Y.append(label)
    print(str(i)+" "+str(len(tweet))+" "+str(label))

X = np.asarray(X)
Y = np.asarray(Y)
np.save("model/X", X)
np.save("model/Y", Y)
'''

X = np.load("model/X.npy")
Y = np.load("model/Y.npy")
print(X[12])
print(Y)

tfidf_vectorizer = TfidfVectorizer(stop_words=stop_words, use_idf=True, smooth_idf=False, norm=None, decode_error='replace', max_features=300)
X = tfidf_vectorizer.fit_transform(X).toarray()


sc = StandardScaler()
X = sc.fit_transform(X)

indices = np.arange(X.shape[0])
np.random.shuffle(indices)
X = X[indices]
Y = Y[indices]

X_train, X_test, y_train, y_test = train_test_split(X, Y, test_size=0.2) #split dataset into train and test

def calculateMetrics(algorithm, predict, y_test):
    label = ['Normal Event', 'Disaster Event']
    a = accuracy_score(y_test,predict)*100
    p = precision_score(y_test, predict,average='macro') * 100
    r = recall_score(y_test, predict,average='macro') * 100
    f = f1_score(y_test, predict,average='macro') * 100
    accuracy.append(a)
    precision.append(p)
    recall.append(r)
    fscore.append(f)

nb_cls = GaussianNB()
nb_cls.fit(X_train, y_train)
predict = nb_cls.predict(X_test)
calculateMetrics("Naive Bayes", predict, y_test)    

knn_cls = KNeighborsClassifier(n_neighbors=2) #create KNN object
knn_cls.fit(X_train, y_train)
predict = knn_cls.predict(X_test)
calculateMetrics("KNN", predict, y_test)   

svm_cls = svm.SVC() #create SVM object
svm_cls.fit(X_train, y_train)
predict = svm_cls.predict(X_test)
calculateMetrics("SVM", predict, y_test)
    
lr_cls = LogisticRegression(max_iter=300) #create Logistic Regression object
lr_cls.fit(X_train, y_train)
predict = lr_cls.predict(X_test)
calculateMetrics("Logistic Regression", predict, y_test)

dt_cls = DecisionTreeClassifier() #create Decision Tree object
dt_cls.fit(X_train, y_train)
predict = dt_cls.predict(X_test)
calculateMetrics("Decision Tree", predict, y_test)

    
rf_cls = RandomForestClassifier() #create Random Forest object
rf_cls.fit(X_train, y_train)
predict = rf_cls.predict(X_test)
calculateMetrics("Random Forest", predict, y_test)

xg_cls = xg.XGBClassifier() #create XGBOost object
xg_cls.fit(X_train, y_train)
predict = xg_cls.predict(X_test)
calculateMetrics("XGBoost", predict, y_test)


X_train1 = np.reshape(X_train, (X_train.shape[0], 10, 10, 3))
X_test1 = np.reshape(X_test, (X_test.shape[0], 10, 10, 3))
y_train1 = to_categorical(y_train)
y_test1 = to_categorical(y_test)

dl_model = Sequential()
dl_model.add(Convolution2D(32, (3 , 3), input_shape = (X_train1.shape[1], X_train1.shape[2], X_train1.shape[3]), activation = 'relu'))
dl_model.add(MaxPooling2D(pool_size = (2, 2)))
dl_model.add(Convolution2D(32, (3, 3), activation = 'relu'))
dl_model.add(MaxPooling2D(pool_size = (2, 2)))
dl_model.add(Flatten())
dl_model.add(Dense(units = 256, activation = 'relu'))
dl_model.add(Dense(units = y_train1.shape[1], activation = 'softmax'))
dl_model.compile(optimizer = 'adam', loss = 'categorical_crossentropy', metrics = ['accuracy'])
dl_model.compile(optimizer = 'adam', loss = 'categorical_crossentropy', metrics = ['accuracy'])  
if os.path.exists("model/dl_weights.hdf5") == False:
    model_check_point = ModelCheckpoint(filepath='model/dl_weights.hdf5', verbose = 1, save_best_only = True)
    hist = dl_model.fit(X_train1, y_train1, batch_size = 16, epochs = 150, validation_data=(X_test1, y_test1), callbacks=[model_check_point], verbose=1)
    f = open('model/dl_history.pckl', 'wb')
    pickle.dump(hist.history, f)
    f.close()    
else:
    dl_model.load_weights("model/dl_weights.hdf5")

predict = dl_model.predict(X_test1)
predict = np.argmax(predict, axis=1)
y_test1 = np.argmax(y_test1, axis=1)
calculateMetrics("DL", predict, y_test1)


def readDetails(contract_type):
    global details
    details = ""
    print(contract_type+"======================")
    web3, contract = get_blockchain_contract()
    if contract_type == 'signup':
        details = contract.functions.getUser().call()
    if contract_type == 'event':
        details = contract.functions.getPost().call()
    print(details)    

def saveDataBlockChain(currentData, contract_type):
    global details
    global contract
    details = ""
    web3, contract = get_blockchain_contract()
    readDetails(contract_type)
    tx_receipt = None
    if contract_type == 'signup':
        details+=currentData
        msg = contract.functions.addUser(details).transact()
        tx_receipt = web3.eth.waitForTransactionReceipt(msg)
    if contract_type == 'event':
        details+=currentData
        post_hash = calculate_post_hash(details)
        msg = contract.functions.setPostWithHash(details, post_hash).transact()
        tx_receipt = web3.eth.waitForTransactionReceipt(msg)
    return tx_receipt   

def Graph(request):
    if request.method == 'GET':
        global precision, recall, fscore, accuracy
        df = pd.DataFrame([['Naive Bayes','Precision',precision[0]],['Naive Bayes','Recall',recall[0]],['Naive Bayes','F1 Score',fscore[0]],['Naive Bayes','Accuracy',accuracy[0]],
                           ['KNN','Precision',precision[1]],['KNN','Recall',recall[1]],['KNN','F1 Score',fscore[1]],['KNN','Accuracy',accuracy[1]],
                           ['SVM','Precision',precision[2]],['SVM','Recall',recall[2]],['SVM','F1 Score',fscore[2]],['SVM','Accuracy',accuracy[2]],
                           ['Logistic Regression','Precision',precision[3]],['Logistic Regression','Recall',recall[3]],['Logistic Regression','F1 Score',fscore[3]],['Logistic Regression','Accuracy',accuracy[3]],
                           ['Decision Tree','Precision',precision[4]],['Decision Tree','Recall',recall[4]],['Decision Tree','F1 Score',fscore[4]],['Decision Tree','Accuracy',accuracy[4]],
                           ['Random Forest','Precision',precision[5]],['Random Forest','Recall',recall[5]],['Random Forest','F1 Score',fscore[5]],['Random Forest','Accuracy',accuracy[5]],
                           ['XGBoost','Precision',precision[6]],['XGBoost','Recall',recall[6]],['XGBoost','F1 Score',fscore[6]],['XGBoost','Accuracy',accuracy[6]],
                           ['Deep Learning (DL)','Precision',precision[7]],['Deep Learning (DL)','Recall',recall[7]],['Deep Learning (DL)','F1 Score',fscore[7]],['Deep Learning (DL)','Accuracy',accuracy[7]],
                          ],columns=['Algorithms','Metrics','Value'])
        df.pivot_table(index="Algorithms", columns="Metrics", values="Value").plot(kind='bar', figsize=(8, 4))
        plt.title("All Algorithms Performance Graph")
        #plt.show()
        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        plt.close()
        img_b64 = base64.b64encode(buf.getvalue()).decode()
        context= {'data': img_b64}
        return render(request, 'ViewGraph.html', context)   

def TrainML(request):
    if request.method == 'GET':
        global precision, recall, fscore, accuracy
        algorithms = ['Naive Bayes', 'KNN', 'SVM', 'Logistic Regression', 'Decision Tree', 'Random Forest', 'XGBoost', 'Deep Learning (DL)']
        output = ""
        for i in range(len(algorithms)):
            output+='<tr><td><font size="" color="black">'+algorithms[i]+'</td>'
            output+='<td><font size="" color="black">'+str(accuracy[i])+'</td>'
            output+='<td><font size="" color="black">'+str(precision[i])+'</td>'
            output+='<td><font size="" color="black">'+str(recall[i])+'</td>'
            output+='<td><font size="" color="black">'+str(fscore[i])+'</td></tr>'
        output+="</table><br/><br/><br/><br/><br/><br/>"
        context= {'data':output}
        return render(request, 'ViewOutput.html', context)    


def ViewTweets(request):
    if request.method == 'GET' or request.method == 'POST':
        from EventApp.supabase_client import get_all_events
        events = get_all_events()

        output = '<h4><b>Detected Events Registry & Blockchain Anchors</b></h4><br/>'

        if not events:
            output += '<p align="center"><font size=3 color="black"><b>No events found.</b></font></p>'
            output += '<br/><br/><br/><br/>'
            context = {'data': output}
            return render(request, 'UserScreen.html', context)

        # Attempt to obtain blockchain contract for status checks
        web3 = None
        contract = None
        try:
            web3, contract = get_blockchain_contract()
        except Exception as e:
            print("[ViewTweets] Warning: Could not connect to blockchain for status check:", e)

        output += '<table border=1 align=center width=98% cellpadding=6 style="background-color: #fdfdfd; border-collapse: collapse; font-size: 12px;">'
        output += '<tr style="background-color: #f5f5f5;">'
        output += '<th><font size=2 color=black>Event ID</font></th>'
        output += '<th><font size=2 color=black>Image</font></th>'
        output += '<th><font size=2 color=black>User</font></th>'
        output += '<th><font size=2 color=black>Tweet / Event Text</font></th>'
        output += '<th><font size=2 color=black>Classification</font></th>'
        output += '<th><font size=2 color=black>Confidence</font></th>'
        output += '<th><font size=2 color=black>Event Date</font></th>'
        output += '<th><font size=2 color=black>SHA-256 Hash</font></th>'
        output += '<th><font size=2 color=black>Trust Score</font></th>'
        output += '<th><font size=2 color=black>Blockchain Tx Hash</font></th>'
        output += '<th><font size=2 color=black>Blockchain Status</font></th>'
        output += '<th><font size=2 color=black>Created At</font></th>'
        output += '<th><font size=2 color=black>Integrity</font></th>'
        output += '</tr>'

        for ev in events:
            ev_id = ev.get('id', '')
            user_val = ev.get('username', 'Anonymous')
            tweet_val = ev.get('tweet', '')
            class_val = ev.get('classification', 'Normal Event Detected')
            conf_val = ev.get('confidence', 0)
            date_val = str(ev.get('event_date', ''))
            sha_val = str(ev.get('sha256_hash', ''))
            score_val = ev.get('trust_score', 0)
            tx_val = ev.get('blockchain_tx_hash')
            created_val = str(ev.get('created_at', ''))[:19].replace('T', ' ')
            img_val = ev.get('image_url')

            is_disaster = "disaster" in str(class_val).lower()
            class_color = "#b71c1c" if is_disaster else "#1b5e20"
            trust_color = "green" if score_val >= 70 else "orange" if score_val > 0 else "red"

            # Image column rendering with graceful fallback for legacy events without images
            if img_val:
                img_display = f'<a href="{img_val}" target="_blank" title="View Full Image"><img src="{img_val}" class="event-table-img" loading="lazy" alt="Event photo" style="width: 44px; height: 44px; object-fit: cover; border-radius: 6px; border: 1px solid rgba(0,242,254,0.35); display: block; margin: 0 auto;"/></a>'
            else:
                img_display = '<span class="no-image-badge" style="font-size: 10px; color: #64748b; font-style: italic;">No image</span>'

            # Check blockchain status for each event
            bc_status = '<font color="gray">Unavailable</font>'
            if contract and ev_id:
                try:
                    data_hash, on_chain_score, timestamp, recorded_by, exists = contract.functions.getEvent(int(ev_id)).call()
                    if not exists:
                        bc_status = '<font color="#e65100"><b>Not Anchored</b></font>'
                    else:
                        bc_hash_hex = data_hash.hex().lower()
                        sb_hash_clean = sha_val.lower().replace('0x', '')
                        if bc_hash_hex == sb_hash_clean:
                            bc_status = '<font color="green"><b>&#10004; VERIFIED</b></font>'
                        else:
                            bc_status = '<font color="red"><b>&#10008; TAMPERED</b></font>'
                except Exception as ex:
                    print(f"[ViewTweets] Blockchain check failed for Event #{ev_id}:", ex)
                    bc_status = '<font color="gray">Unavailable</font>'
            elif not contract:
                bc_status = '<font color="gray">RPC Unavailable</font>'

            tx_display = f'<code style="font-size: 10px; word-break: break-all;">{tx_val}</code>' if tx_val else '<font color="gray"><i>Not recorded</i></font>'
            sha_display = f'<code style="font-size: 10px; word-break: break-all;">{sha_val}</code>' if sha_val else '<font color="gray"><i>N/A</i></font>'
            verify_btn = f'<a href="/VerifyIntegrity?event_id={ev_id}" style="background-color: #1976d2; color: #ffffff; padding: 3px 8px; font-size: 11px; text-decoration: none; border-radius: 3px; font-weight: bold; white-space: nowrap;">Verify</a>'

            output += '<tr>'
            output += f'<td align=center><b>#{ev_id}</b></td>'
            output += f'<td align=center>{img_display}</td>'
            output += f'<td><b>{user_val}</b></td>'
            output += f'<td style="max-width: 280px; word-wrap: break-word;"><i>"{tweet_val}"</i></td>'
            output += f'<td><font color="{class_color}"><b>{class_val}</b></font></td>'
            output += f'<td align=center>{round(float(conf_val), 2)}%</td>'
            output += f'<td align=center>{date_val}</td>'
            output += f'<td style="max-width: 140px; word-break: break-all;">{sha_display}</td>'
            output += f'<td align=center><font color="{trust_color}"><b>{score_val} / 100</b></font></td>'
            output += f'<td style="max-width: 140px; word-break: break-all;">{tx_display}</td>'
            output += f'<td align=center>{bc_status}</td>'
            output += f'<td align=center style="white-space: nowrap;"><font size=1 color=gray>{created_val}</font></td>'
            output += f'<td align=center>{verify_btn}</td>'
            output += '</tr>'

        output += '</table><br/><br/><br/><br/>'
        context = {'data': output}
        return render(request, 'UserScreen.html', context)


def PredictAction(request):
    if request.method == 'POST':
        global username
        tweet = request.POST.get('t1', False)
        data = tweet.strip().lower()
        data = cleanText(data)
        temp = []
        temp.append(data)
        temp = tfidf_vectorizer.transform(temp).toarray()
        dl_model = load_model("model/dl_weights.hdf5")
        temp = sc.transform(temp)
        temp = np.reshape(temp, (temp.shape[0], 10, 10, 3))
        predict = dl_model.predict(temp)
        predict_probs = predict[0]  #get probabilities [P(normal), P(disaster)]
        predict = np.argmax(predict_probs)
        confidence = float(predict_probs[predict]) * 100
        print(predict)
        print("Class:", predict, "| Confidence:", round(confidence, 2), "%")
        output = "Normal Event Detected"
        is_disaster = False
        if predict == 1:
            output = "Disaster Event Detected"
            is_disaster = True
        today = date.today()
        user_val = username if username else "Anonymous"

        # Format event data string and compute local SHA-256 cryptographic digest
        post_str = user_val + "$" + tweet + "$" + str(today) + "$" + output + "\n"
        post_hash_bytes = calculate_post_hash(post_str)
        sha256_clean = post_hash_bytes.hex()

        # Calculate explainable trust score (initial prediction has verified data integrity)
        trust_score = calculate_trust_score(verified=True, confidence=confidence, is_disaster=is_disaster)

        # 1. Inspect optional local image upload and validate server-side
        uploaded_file = request.FILES.get('event_image', None)
        image_url = None
        if uploaded_file:
            # A. Enforce maximum 5 MB file size limit
            MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5 MB
            if uploaded_file.size > MAX_IMAGE_SIZE:
                context = {
                    'error_message': 'Uploaded file exceeds the maximum 5 MB limit. Please select an image under 5 MB.',
                    'data': None
                }
                return render(request, 'Predict.html', context)

            # B. Enforce allowed image extension whitelist
            allowed_extensions = {'.jpg', '.jpeg', '.png', '.webp'}
            ext = os.path.splitext(uploaded_file.name)[1].lower()
            if ext not in allowed_extensions:
                context = {
                    'error_message': f'Invalid file format ({ext}). Only JPG, JPEG, PNG, and WEBP image files are allowed.',
                    'data': None
                }
                return render(request, 'Predict.html', context)

            # C. Generate safe UUID-based filename (never trust raw client filename)
            clean_basename = re.sub(r'[^a-zA-Z0-9_\.-]', '_', os.path.basename(uploaded_file.name))
            safe_filename = f"evt_{uuid.uuid4().hex[:12]}_{clean_basename}"
            content_type = getattr(uploaded_file, 'content_type', 'image/jpeg')

            # D. Server-side upload to Supabase Storage bucket 'event-images'
            from EventApp.supabase_client import upload_event_image
            upload_res = upload_event_image(uploaded_file, safe_filename, content_type=content_type)
            if not upload_res.get('success'):
                err_text = upload_res.get('error', 'Storage upload failure')
                print(f"[Supabase Storage Error] Image upload failed: {err_text}")
                context = {
                    'error_message': f'Image upload to Supabase Storage failed: {err_text}. Event was NOT recorded.',
                    'data': None
                }
                return render(request, 'Predict.html', context)
            
            image_url = upload_res.get('image_url')
            print(f"[Supabase Storage Success] Image uploaded successfully: {image_url}")

        # 2. Insert event into Supabase FIRST to obtain unique event_id
        from EventApp.supabase_client import insert_event, update_event_tx_hash
        sp_res = insert_event(
            username=user_val,
            tweet=tweet,
            classification=output,
            confidence=confidence,
            event_date=today,
            sha256_hash=sha256_clean,
            trust_score=trust_score,
            blockchain_tx_hash=None,
            user_id=None,
            image_url=image_url
        )

        event_id = None
        if sp_res and sp_res.get('success') and 'data' in sp_res and 'id' in sp_res['data']:
            event_id = int(sp_res['data']['id'])
            print(f"[Supabase Success] Event persisted with ID: {event_id}")
        else:
            err_msg = sp_res.get('error', 'Unknown error') if sp_res else 'No response'
            print(f"[Supabase Warning] Event persistence failed: {err_msg}")

        # 3. Commit to Ethereum using the event-specific recordEvent function
        tx_hash_hex = None
        if event_id is not None:
            try:
                web3, contract = get_blockchain_contract()
                tx = contract.functions.recordEvent(
                    int(event_id),
                    post_hash_bytes,
                    int(trust_score)
                ).transact()
                tx_receipt = web3.eth.waitForTransactionReceipt(tx)
                if tx_receipt and 'transactionHash' in tx_receipt:
                    tx_hash_hex = tx_receipt['transactionHash'].hex()
                    print(f"[Blockchain Success] Event {event_id} anchored on Ethereum. Tx: {tx_hash_hex}")

                    # 4. Update Supabase event row with the Ethereum transaction hash
                    upd_res = update_event_tx_hash(event_id, tx_hash_hex)
                    if not upd_res.get('success'):
                        print(f"[Supabase Warning] Could not update tx_hash for event {event_id}: {upd_res.get('error')}")
            except Exception as eth_err:
                print(f"[Blockchain Error] Ethereum recordEvent failed for event {event_id}: {eth_err}")
        else:
            print("[Blockchain Warning] Skipping Ethereum recordEvent because event_id is None.")

        image_html = f"<br/><b>Attached Image :</b> <a href='{image_url}' target='_blank' style='color: #00f2fe; text-decoration: underline; font-weight: 600;'>View Uploaded Photo</a>" if image_url else ""
        context = {
            'data': f"<b>Post Classified as :</b> {output}<br/>"
                    f"<b>Model Confidence :</b> {round(confidence, 2)}%<br/>"
                    f"<b>Data Integrity :</b> VERIFIED &#10004;<br/>"
                    f"<b>Trust Score (Stored on Blockchain) :</b> {trust_score} / 100"
                    f"{image_html}",
            'image_url': image_url
        }
        return render(request, 'Predict.html', context)         

def Predict(request):
    if request.method == 'GET':
       return render(request, 'Predict.html', {})    

def index(request):
    if request.method == 'GET':
       return render(request, 'index.html', {})    

def UserLogin(request):
    if request.method == 'GET':
       return render(request, 'UserLogin.html', {})

def Register(request):
    if request.method == 'GET':
       return render(request, 'Register.html', {})

def RegisterAction(request):
    if request.method == 'POST':
        username = request.POST.get('t1', False)
        password = request.POST.get('t2', False)
        contact = request.POST.get('t3', False)
        email = request.POST.get('t4', False)
        address = request.POST.get('t5', False)
        record = 'none'
        readDetails("signup")
        rows = details.split("\n")
        for i in range(len(rows)-1):
            arr = rows[i].split("#")
            if arr[0] == "signup":
                if arr[1] == username:
                    record = "exists"
                    break
        if record == 'none':
            data = "signup#"+username+"#"+password+"#"+contact+"#"+email+"#"+address+"\n"
            saveDataBlockChain(data,"signup")
            context= {'data':'Signup process completd and record saved in Blockchain'}
            return render(request, 'Register.html', context)
        else:
            context= {'data':username+'Username already exists'}
            return render(request, 'Register.html', context)    

def UserLoginAction(request):
    if request.method == 'POST':
        global username
        username = request.POST.get('t1', False)
        password = request.POST.get('t2', False)
        status = "UserLogin.html"
        context= {'data':'Invalid login details'}
        readDetails("signup")
        rows = details.split("\n")
        for i in range(len(rows)-1):
            arr = rows[i].split("#")
            if arr[0] == "signup":
                if arr[1] == username and arr[2] == password:
                    context = {'data':"Welcome "+username}
                    status = 'UserScreen.html'
                    break
        return render(request, status, context)              


#verify data integrity by comparing local SHA-256 hash with blockchain-stored hash
def verify_post_integrity(event_id=None, custom_event=None):
    """
    Phase 6 Event-Oriented Integrity Verification:
    Supabase event ID -> Ethereum getEvent(event_id) -> retrieve dataHash & trustScore ->
    calculate/obtain expected SHA-256 hash -> compare Supabase hash with blockchain dataHash ->
    VERIFIED, TAMPERED / UNVERIFIED, or NOT ANCHORED / UNVERIFIED.
    Hard gate: If integrity fails, trust score = 0.
    """
    web3, contract = get_blockchain_contract()
    target_event = None

    # 1. Identify the event being verified using Supabase event ID
    if custom_event is not None:
        target_event = custom_event
        if event_id is None and target_event and 'id' in target_event:
            event_id = target_event['id']
    elif event_id is not None:
        from EventApp.supabase_client import get_event
        try:
            target_event = get_event(int(event_id))
        except Exception as e:
            print(f"[Verification] Error fetching event #{event_id} from Supabase: {e}")
            target_event = None
    else:
        from EventApp.supabase_client import get_latest_event
        try:
            target_event = get_latest_event()
            if target_event and 'id' in target_event:
                event_id = target_event['id']
        except Exception as e:
            print("[Verification] Error fetching latest event from Supabase:", e)
            target_event = None

    # Fallback if event_id is still unknown: query blockchain latestEventId
    if event_id is None:
        try:
            latest_id = contract.functions.latestEventId().call()
            if latest_id > 0:
                event_id = latest_id
                from EventApp.supabase_client import get_event
                target_event = get_event(event_id)
        except Exception:
            pass

    # If no event can be identified at all
    if event_id is None:
        return {
            'verified': False,
            'status': 'NOT ANCHORED / UNVERIFIED',
            'message': 'No event record found to verify',
            'event_id': None,
            'local_hash': '0x' + '0'*64,
            'blockchain_hash': '0x' + '0'*64,
            'post_data': '',
            'trust_score': 0,
            'on_chain_trust_score': 0,
            'latest_user': '',
            'latest_tweet': '',
            'latest_date': '',
            'latest_class': 'Normal Event Detected',
            'is_disaster': False,
            'timestamp': 0,
            'recorded_by': '',
            'exists': False
        }

    # 2. Retrieve event from Ethereum mapping using getEvent(event_id)
    try:
        data_hash_bytes, on_chain_trust_score, timestamp, recorded_by, exists = contract.functions.getEvent(int(event_id)).call()
    except Exception as e:
        print(f"[Verification] Ethereum getEvent({event_id}) call failed: {e}")
        return {
            'verified': False,
            'status': 'NOT ANCHORED / UNVERIFIED',
            'message': f'Blockchain query failed for Event #{event_id}: {str(e)}',
            'event_id': event_id,
            'local_hash': '0x' + '0'*64,
            'blockchain_hash': '0x' + '0'*64,
            'post_data': '',
            'trust_score': 0,
            'on_chain_trust_score': 0,
            'latest_user': target_event.get('username', '') if target_event else '',
            'latest_tweet': target_event.get('tweet', '') if target_event else '',
            'latest_date': str(target_event.get('event_date', '')) if target_event else '',
            'latest_class': target_event.get('classification', 'Normal Event Detected') if target_event else 'Normal Event Detected',
            'is_disaster': ('disaster' in target_event.get('classification', '').lower()) if target_event else False,
            'timestamp': 0,
            'recorded_by': '',
            'exists': False
        }

    # 3. Check if event exists on the blockchain
    if not exists:
        local_hash_hex = '0x' + '0'*64
        post_data = ''
        if target_event:
            post_data = f"{target_event.get('username','')}${target_event.get('tweet','')}${target_event.get('event_date','')}${target_event.get('classification','')}\n"
            local_hash_hex = "0x" + calculate_post_hash(post_data).hex()

        return {
            'verified': False,
            'status': 'NOT ANCHORED / UNVERIFIED',
            'message': f'EVENT NOT ANCHORED / UNVERIFIED - Event #{event_id} has not been recorded on Ethereum blockchain',
            'event_id': event_id,
            'local_hash': local_hash_hex,
            'blockchain_hash': '0x' + '0'*64,
            'post_data': post_data,
            'trust_score': 0,
            'on_chain_trust_score': 0,
            'latest_user': target_event.get('username', '') if target_event else '',
            'latest_tweet': target_event.get('tweet', '') if target_event else '',
            'latest_date': str(target_event.get('event_date', '')) if target_event else '',
            'latest_class': target_event.get('classification', 'Normal Event Detected') if target_event else 'Normal Event Detected',
            'is_disaster': ('disaster' in target_event.get('classification', '').lower()) if target_event else False,
            'timestamp': 0,
            'recorded_by': '',
            'exists': False
        }

    # 4. Event exists on-chain: retrieve blockchain dataHash and trustScore
    blockchain_hash_hex = "0x" + data_hash_bytes.hex()

    # If event exists on chain but is missing from Supabase
    if not target_event:
        return {
            'verified': False,
            'status': 'TAMPERED / UNVERIFIED',
            'message': f'DATA TAMPERED / UNVERIFIED - Event #{event_id} exists on blockchain but record missing from database',
            'event_id': event_id,
            'local_hash': '0x' + '0'*64,
            'blockchain_hash': blockchain_hash_hex,
            'post_data': '',
            'trust_score': 0,
            'on_chain_trust_score': int(on_chain_trust_score),
            'latest_user': '',
            'latest_tweet': '',
            'latest_date': '',
            'latest_class': 'Normal Event Detected',
            'is_disaster': False,
            'timestamp': timestamp,
            'recorded_by': recorded_by,
            'exists': True
        }

    # Reconstruct expected event post string and calculate local SHA-256 hash
    post_data = f"{target_event.get('username','')}${target_event.get('tweet','')}${target_event.get('event_date','')}${target_event.get('classification','')}\n"
    local_hash_bytes = calculate_post_hash(post_data)
    local_hash_hex = "0x" + local_hash_bytes.hex()

    # Compare Supabase hash with blockchain dataHash
    supabase_hash = str(target_event.get('sha256_hash', '')).lower()
    if supabase_hash.startswith('0x'):
        supabase_hash = supabase_hash[2:]

    hash_match = (local_hash_bytes == data_hash_bytes) and (supabase_hash == data_hash_bytes.hex().lower())

    if hash_match:
        verified = True
        status = 'VERIFIED'
        message = f'DATA INTEGRITY VERIFIED - Supabase SHA-256 hash matches Ethereum on-chain proof for Event #{event_id}'
        # If integrity succeeds: use the stored/verified trust score
        final_trust_score = int(on_chain_trust_score)
    else:
        verified = False
        status = 'TAMPERED / UNVERIFIED'
        message = f'DATA TAMPERED / UNVERIFIED - Supabase hash ({local_hash_hex}) does not match Ethereum blockchain dataHash ({blockchain_hash_hex}) for Event #{event_id}'
        # If integrity fails: Trust Score = 0 (hard gate)
        final_trust_score = 0

    latest_user = target_event.get('username', '')
    latest_tweet = target_event.get('tweet', '')
    latest_date = str(target_event.get('event_date', ''))
    latest_class = target_event.get('classification', 'Normal Event Detected')
    is_disaster = ('disaster' in latest_class.lower())

    return {
        'verified': verified,
        'status': status,
        'message': message,
        'event_id': event_id,
        'local_hash': local_hash_hex,
        'blockchain_hash': blockchain_hash_hex,
        'post_data': post_data,
        'trust_score': final_trust_score,
        'on_chain_trust_score': int(on_chain_trust_score),
        'latest_user': latest_user,
        'latest_tweet': latest_tweet,
        'latest_date': latest_date,
        'latest_class': latest_class,
        'is_disaster': is_disaster,
        'timestamp': timestamp,
        'recorded_by': recorded_by,
        'exists': True
    }


# Server-side persistent Demo/Test Mode backup storage
# Captures pre-tamper legitimate event ID, blockchain hash, and trust score
DEMO_BACKUP_FILE = 'demo_backup.json'

def get_demo_backup(event_id=None):
    """Load demo backup from persistent JSON file for a specific event_id or latest."""
    if os.path.exists(DEMO_BACKUP_FILE):
        try:
            with open(DEMO_BACKUP_FILE, 'r') as f:
                data = json.load(f)
                if not isinstance(data, dict):
                    return None
                if event_id is not None:
                    str_id = str(event_id)
                    if str_id in data and isinstance(data[str_id], dict):
                        return data[str_id]
                    if data.get('event_id') == int(event_id):
                        return data
                    return None
                if 'latest_tampered_event_id' in data:
                    latest_id = str(data['latest_tampered_event_id'])
                    if latest_id in data and isinstance(data[latest_id], dict):
                        return data[latest_id]
                return data
        except Exception as e:
            print("Error reading demo backup file:", e)
    return None

def save_demo_backup(event_id, original_hash, original_trust_score, post_str=""):
    """
    Save event-specific demo backup to file for persistent restoration.
    Stores: event_id, original_hash, original_trust_score.
    """
    try:
        backups = {}
        if os.path.exists(DEMO_BACKUP_FILE):
            try:
                with open(DEMO_BACKUP_FILE, 'r') as f:
                    content = json.load(f)
                    if isinstance(content, dict):
                        backups = content
            except Exception:
                backups = {}

        clean_hash = str(original_hash)
        if not clean_hash.startswith("0x"):
            clean_hash = "0x" + clean_hash

        entry = {
            'event_id': int(event_id),
            'original_hash': clean_hash,
            'original_trust_score': int(original_trust_score),
            'hash': clean_hash,
            'trust_score': int(original_trust_score),
            'post': post_str
        }

        backups[str(event_id)] = entry
        backups['latest_tampered_event_id'] = int(event_id)
        backups['event_id'] = int(event_id)
        backups['original_hash'] = clean_hash
        backups['original_trust_score'] = int(original_trust_score)
        backups['hash'] = clean_hash
        backups['trust_score'] = int(original_trust_score)
        backups['post'] = post_str

        with open(DEMO_BACKUP_FILE, 'w') as f:
            json.dump(backups, f, indent=2)
    except Exception as e:
        print("Error saving demo backup file:", e)

def VerifyIntegrity(request):
    if request.method == 'GET' or request.method == 'POST':
        req_event_id = request.GET.get('event_id') or request.POST.get('event_id')
        if req_event_id:
            try:
                req_event_id = int(req_event_id)
            except (ValueError, TypeError):
                req_event_id = None
        result = verify_post_integrity(req_event_id)
        demo_status = request.GET.get('demo_status', '')

        if result['status'] == 'VERIFIED':
            status_icon = '&#10004;'  # checkmark
            status_text = 'VERIFIED'
            status_color = 'green'
            trust_color = 'green' if result['trust_score'] >= 70 else 'orange'
        elif result['status'] == 'NOT ANCHORED / UNVERIFIED':
            status_icon = '&#9888;'   # warning symbol
            status_text = 'NOT ANCHORED / UNVERIFIED'
            status_color = '#e65100'  # amber
            trust_color = 'red'
            result['trust_score'] = 0
        else:
            status_icon = '&#10008;'  # cross
            status_text = 'TAMPERED / UNVERIFIED'
            status_color = 'red'
            trust_color = 'red'
            result['trust_score'] = 0

        # Calculate model confidence for the post
        confidence_display = "N/A"
        if result['latest_tweet']:
            try:
                data_clean = cleanText(result['latest_tweet'].strip().lower())
                temp = [data_clean]
                temp = tfidf_vectorizer.transform(temp).toarray()
                dl_m = load_model("model/dl_weights.hdf5")
                temp = sc.transform(temp)
                temp = np.reshape(temp, (temp.shape[0], 10, 10, 3))
                pred = dl_m.predict(temp)
                p_probs = pred[0]
                idx = np.argmax(p_probs)
                conf = float(p_probs[idx]) * 100
                confidence_display = f"{round(conf, 2)}%"
            except Exception as e:
                print("Error calculating confidence for verification display:", e)
                confidence_display = "N/A"

        output = '<h4><b>Blockchain Event Trust Verification & Data Integrity</b></h4><br/>'

        # Optional notification banner for Demo actions
        target_display_id = result.get("event_id")
        id_str = f" for Event #{target_display_id}" if target_display_id is not None else ""
        if demo_status == 'tampered':
            output += '<div style="background-color: #ffebee; border: 1px solid #ef5350; color: #b71c1c; padding: 10px; border-radius: 4px; width: 85%; margin: 0 auto 15px auto; text-align: center; font-size: 11pt;">'
            output += f'<b>⚠️ DEMO TAMPERING EXECUTED{id_str}:</b> Blockchain cryptographic proof hash was modified to <code>0xdeadbeef...</code> via <code>simulateEventTampering()</code>. The cryptographic integrity gate failed, forfeiting the Trust Score to <b>0 / 100</b>.'
            output += '</div>'
        elif demo_status == 'restored':
            output += '<div style="background-color: #e8f5e9; border: 1px solid #66bb6a; color: #1b5e20; padding: 10px; border-radius: 4px; width: 85%; margin: 0 auto 15px auto; text-align: center; font-size: 11pt;">'
            output += f'<b>✅ DEMO RESTORATION SUCCESSFUL{id_str}:</b> The authentic SHA-256 hash and trust score were restored to the Ethereum blockchain via <code>restoreEvent()</code>. Data integrity is <b>VERIFIED &#10004;</b> and Trust Score is restored!'
            output += '</div>'
        elif demo_status == 'no_backup':
            output += '<div style="background-color: #fff3e0; border: 1px solid #ffa726; color: #e65100; padding: 10px; border-radius: 4px; width: 85%; margin: 0 auto 15px auto; text-align: center; font-size: 11pt;">'
            output += '<b>ℹ️ NO DEMO BACKUP FOUND:</b> No prior pre-tamper event backup is currently stored. Please post an event via <a href="/Predict.html">Predict</a> first before testing tamper simulation.'
            output += '</div>'
        elif demo_status == 'error':
            output += '<div style="background-color: #ffebee; border: 1px solid #ef5350; color: #b71c1c; padding: 10px; border-radius: 4px; width: 85%; margin: 0 auto 15px auto; text-align: center; font-size: 11pt;">'
            output += '<b>⚠️ DEMO ACTION ERROR:</b> Could not communicate with the smart contract at http://127.0.0.1:9545. Ensure Truffle Develop blockchain is running.'
            output += '</div>'

        output += '<table border=1 align=center width=85% cellpadding=8 style="background-color: #fdfdfd; border-collapse: collapse;">'

        if result.get('event_id') is not None:
            output += '<tr><td width=35%><font size=3 color=black><b>Event ID</b></font></td>'
            output += f'<td><font size=3 color=black><b>#{result["event_id"]}</b> <font size=2 color=gray>(Ethereum Registry & Supabase)</font></font></td></tr>'

        output += '<tr><td width=35%><font size=3 color=black><b>Data Integrity</b></font></td>'
        output += f'<td><font size=4 color="{status_color}"><b>{status_icon} {status_text}</b></font></td></tr>'
        
        output += '<tr><td><font size=3 color=black><b>Trust Score</b></font></td>'
        output += f'<td><font size=4 color="{trust_color}"><b>{result["trust_score"]} / 100</b></font> '
        if result['status'] == 'VERIFIED':
            output += '<font size=2 color=gray>(Integrity: 50 | DL Confidence: 40 max | Event Context: 10 max)</font>'
        elif result['status'] == 'NOT ANCHORED / UNVERIFIED':
            output += '<font size=2 color=red>(Score forfeited: Event is not anchored on Ethereum)</font>'
        else:
            output += '<font size=2 color=red>(Score forfeited: Integrity mismatch detected)</font>'
        output += '</td></tr>'
        
        output += '<tr><td><font size=3 color=black><b>Classification</b></font></td>'
        output += f'<td><font size=3 color=black><b>{result["latest_class"]}</b></font></td></tr>'
        
        output += '<tr><td><font size=3 color=black><b>Confidence</b></font></td>'
        output += f'<td><font size=3 color=black><b>{confidence_display}</b></font></td></tr>'

        if result['latest_tweet']:
            output += '<tr><td><font size=3 color=black><b>Latest Stored Post</b></font></td>'
            output += f'<td><font size=2 color=black><i>"{result["latest_tweet"]}"</i> (by: <b>{result["latest_user"]}</b> on {result["latest_date"]})</font></td></tr>'
        elif result['post_data']:
            output += '<tr><td><font size=3 color=black><b>Latest Stored Post</b></font></td>'
            output += f'<td><font size=2 color=red><b>[ALTERED RECORD]</b> <code>{result["post_data"]}</code></font></td></tr>'

        output += '<tr><td><font size=3 color=black><b>Blockchain Hash</b></font></td>'
        output += f'<td><font size=2 color=black><code style="word-break: break-all;">{result["blockchain_hash"]}</code></font></td></tr>'

        output += '<tr><td><font size=3 color=black><b>Local Hash</b></font></td>'
        output += f'<td><font size=2 color=black><code style="word-break: break-all;">{result["local_hash"]}</code></font></td></tr>'
        
        output += '<tr><td><font size=3 color=black><b>Verification Message</b></font></td>'
        output += f'<td><font size=2 color=black>{result["message"]}</font></td></tr>'
        
        output += '</table><br/>'

        curr_ev_id = result.get("event_id")
        curr_ev_str = str(curr_ev_id) if curr_ev_id is not None else ""

        # DEMO / TEST MODE Section
        output += '<table border=1 align=center width=85% cellpadding=10 style="background-color: #fff9f9; border: 2px dashed #c62828; border-collapse: collapse;">'
        output += '<tr><td colspan=2 align=center style="background-color: #ffebee;">'
        output += '<font size=3 color="#b71c1c"><b>🔬 DEMO / TEST MODE &mdash; Event-Specific Tamper Simulation</b></font><br/>'
        if curr_ev_str:
            output += f'<font size=2 color="#333"><b>Target Event ID: #{curr_ev_str}</b> (Ethereum Registry & Supabase)</font><br/>'
        output += '<font size=2 color="#555">Demonstrate smart contract tamper detection and cryptographic integrity verification directly from the browser without modifying contract code or ML model.</font>'
        output += '</td></tr>'
        
        output += '<tr>'
        output += '<td width=50% align=center style="padding: 14px;">'
        output += '<form method="POST" action="/SimulateTamper" style="margin: 0;" onsubmit="return confirm(\'DEMO MODE: This will alter the cryptographic proof hash on Ethereum for Event #' + curr_ev_str + ' to a tampered hash. The integrity check will fail and trust score will become 0. Proceed?\');">'
        if curr_ev_str:
            output += f'<input type="hidden" name="event_id" value="{curr_ev_str}">'
        output += '<input type="submit" value="⚠️ Simulate Blockchain Tampering" style="background-color: #c62828; color: #ffffff; padding: 10px 18px; font-size: 13px; font-weight: bold; border: 1px solid #8e0000; border-radius: 4px; cursor: pointer;">'
        output += '</form><br/>'
        output += f'<font size=2 color="#666">Alters <code>dataHash</code> on Ethereum for Event #{curr_ev_str} via <code>simulateEventTampering()</code> and resets on-chain trust score to 0.</font>'
        output += '</td>'
        
        output += '<td width=50% align=center style="padding: 14px;">'
        output += '<form method="POST" action="/RestoreEvent" style="margin: 0;">'
        if curr_ev_str:
            output += f'<input type="hidden" name="event_id" value="{curr_ev_str}">'
        output += '<input type="submit" value="🔄 Restore Original Event" style="background-color: #2e7d32; color: #ffffff; padding: 10px 18px; font-size: 13px; font-weight: bold; border: 1px solid #1b5e20; border-radius: 4px; cursor: pointer;">'
        output += '</form><br/>'
        output += f'<font size=2 color="#666">Restores the authentic SHA-256 hash and trust score for Event #{curr_ev_str} via <code>restoreEvent()</code>.</font>'
        output += '</td>'
        output += '</tr>'
        output += '</table><br/><br/><br/><br/>'

        context = {'data': output}
        return render(request, 'UserScreen.html', context)

@csrf_exempt
def SimulateTamper(request):
    """
    DEMO / TEST MODE ONLY (Phase 7 Event-Oriented Tamper Simulation):
    1. Identify selected or latest Supabase event ID.
    2. Retrieve authentic blockchain record using getEvent(event_id).
    3. Save original values for restoration: event_id, original_hash, original_trust_score.
    4. Generate controlled tampered hash (bytes32).
    5. Call smart contract simulateEventTampering(event_id, tampered_hash).
    6. Redirect to VerifyIntegrity to verify TAMPERED / UNVERIFIED and Trust Score 0.
    """
    try:
        target_event_id = request.POST.get('event_id') or request.GET.get('event_id')
        if target_event_id:
            try:
                target_event_id = int(target_event_id)
            except (ValueError, TypeError):
                target_event_id = None

        if target_event_id is None:
            from EventApp.supabase_client import get_latest_event
            latest_ev = get_latest_event()
            if latest_ev and 'id' in latest_ev:
                target_event_id = int(latest_ev['id'])

        web3, contract = get_blockchain_contract()

        if target_event_id is None:
            latest_id = contract.functions.latestEventId().call()
            if latest_id > 0:
                target_event_id = int(latest_id)

        if target_event_id is None:
            return redirect('/VerifyIntegrity?demo_status=error')

        # Retrieve authentic on-chain record
        data_hash_bytes, on_chain_trust_score, timestamp, recorded_by, exists = contract.functions.getEvent(target_event_id).call()
        if not exists:
            return redirect(f'/VerifyIntegrity?event_id={target_event_id}&demo_status=error')

        # Save legitimate pre-tamper state
        existing_backup = get_demo_backup(target_event_id)
        if not existing_backup or existing_backup.get('original_trust_score', 0) == 0:
            if on_chain_trust_score > 0:
                save_demo_backup(
                    event_id=target_event_id,
                    original_hash="0x" + data_hash_bytes.hex(),
                    original_trust_score=int(on_chain_trust_score)
                )

        # Generate controlled tampered hash
        tampered_hash_bytes = bytes.fromhex("deadbeef" * 8)

        # Call contract simulateEventTampering
        tx = contract.functions.simulateEventTampering(target_event_id, tampered_hash_bytes).transact()
        web3.eth.waitForTransactionReceipt(tx)

        return redirect(f'/VerifyIntegrity?event_id={target_event_id}&demo_status=tampered')
    except Exception as e:
        print("[SimulateTamper Error]:", e)
        return redirect('/VerifyIntegrity?demo_status=error')

@csrf_exempt
def RestoreEvent(request):
    """
    DEMO / TEST MODE ONLY (Phase 7 Event-Oriented Restoration):
    1. Identify target event ID from request or backup.
    2. Retrieve original hash and original trust score from demo_backup.json (and Supabase).
    3. Call smart contract restoreEvent(event_id, original_hash, original_trust_score).
    4. Redirect to VerifyIntegrity to verify VERIFIED status and restored Trust Score.
    """
    try:
        target_event_id = request.POST.get('event_id') or request.GET.get('event_id')
        if target_event_id:
            try:
                target_event_id = int(target_event_id)
            except (ValueError, TypeError):
                target_event_id = None

        backup = get_demo_backup(target_event_id)
        if not backup:
            backup = get_demo_backup()

        restore_event_id = target_event_id
        if restore_event_id is None and backup:
            restore_event_id = backup.get('event_id')

        if restore_event_id is None:
            from EventApp.supabase_client import get_latest_event
            latest_ev = get_latest_event()
            if latest_ev and 'id' in latest_ev:
                restore_event_id = int(latest_ev['id'])

        if restore_event_id is None:
            return redirect('/VerifyIntegrity?demo_status=no_backup')

        # Obtain original hash and score from backup or Supabase record
        orig_hash_hex = None
        orig_score = None

        if backup:
            orig_hash_hex = backup.get('original_hash') or backup.get('hash')
            orig_score = backup.get('original_trust_score') or backup.get('trust_score')

        from EventApp.supabase_client import get_event
        sb_ev = get_event(int(restore_event_id))
        if sb_ev:
            if not orig_hash_hex and sb_ev.get('sha256_hash'):
                orig_hash_hex = sb_ev['sha256_hash']
            if (orig_score is None or orig_score == 0) and sb_ev.get('trust_score'):
                orig_score = sb_ev['trust_score']

        if not orig_hash_hex or orig_score is None:
            return redirect(f'/VerifyIntegrity?event_id={restore_event_id}&demo_status=no_backup')

        clean_hash = orig_hash_hex
        if clean_hash.startswith("0x"):
            clean_hash = clean_hash[2:]
        orig_hash_bytes = bytes.fromhex(clean_hash)

        web3, contract = get_blockchain_contract()
        tx = contract.functions.restoreEvent(
            int(restore_event_id),
            orig_hash_bytes,
            int(orig_score)
        ).transact()
        web3.eth.waitForTransactionReceipt(tx)

        return redirect(f'/VerifyIntegrity?event_id={restore_event_id}&demo_status=restored')
    except Exception as e:
        print("[RestoreEvent Error]:", e)
        return redirect('/VerifyIntegrity?demo_status=error')


