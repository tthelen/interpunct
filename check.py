import tablib
import hashlib

data = tablib.Dataset().load(open('data/user.csv').read(), format='csv')
users={}
for d in data:
    users[d[0].encode("ascii")] = d[1]
print("{} Nutzer eingelesen.".format(len(users)))

participants = tablib.Dataset().load(open('data/seminar_grimm.csv').read(), format='csv')
print("{} Teilnehmerdaten eingelesen.".format(len(participants)))

with open("data/from_ortho_sem.csv", "a") as fos:

    result = tablib.Dataset()
    result.headers = ["Vorname", "Nachname", "Benutzername"]
    result_neg = tablib.Dataset()
    result_neg.headers = ["Vorname", "Nachname", "Benutzername"]
    for p in participants:
        hash = bytes(hashlib.md5((p[3]+"f2ad53d33b74590627077cb6a273df38").encode("ascii")).hexdigest(),'ascii')
        if hash in users:
            fos.write(hash.decode("ascii")+"\n")
            if int(users[hash])>20:
                result.append([p[0],p[1],p[2]])
        if hash not in users or int(users[hash])<21:
            result_neg.append([p[0],p[1],p[2]])
with open("data/kommkoenige_grimm.csv","w") as f:
    f.write(result.csv)
with open("data/kommkoenige_neg_grimm.csv","w") as f:
    f.write(result_neg.csv)

print("{} Teilnehmer haben die Stufe 'Kommakönig' erreicht.".format(len(result.dict)))

