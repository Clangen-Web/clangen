import platform

def writeFile(filename, content):
    openrequest = platform.window.indexedDB.open(filename, 4)

    openrequest.onsuccess = lambda event: writeFileSuccess(event, content)



    def writeFileSuccess(event, content):
        db = event.target.result
        transaction = db.transaction(["files"], "readwrite")
        store = transaction.objectStore("files")
        store.put(content, filename)
        transaction.oncomplete = lambda event: writeFileComplete(event, filename)