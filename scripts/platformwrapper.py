# pylint: disable=no-member
import platform
from sys import platform as _platform
if _platform == "emscripten":
    is_web = True
else:
    is_web = False
del _platform



def reload():
    if not is_web:
        return
    platform.window.location.reload()

def pushdb():
    if not is_web:
        return
    platform.window.FS.syncfs(False, platform.window.console.log)

def pulldb():
    if not is_web:
        return
    platform.window.FS.syncfs(True, platform.window.console.log)

def _is_web():
    return is_web

def eval(code):
    if not is_web:
        return
    platform.window.eval(code)

def init_idbfs():
    if not is_web:
        return
    #minified, copied from https://github.com/emscripten-core/emscripten/blob/main/src/library_idbfs.js
    eval("""window.IDBFS={dbs:{},indexedDB(){if("undefined"!=typeof indexedDB)return indexedDB;var e=null;return"object"==typeof window&&(e=window.indexedDB||window.mozIndexedDB||window.webkitIndexedDB||window.msIndexedDB),assert(e,"IDBFS used, but indexedDB not supported"),e},DB_VERSION:21,DB_STORE_NAME:"FILE_DATA",mount:function(e){return MEMFS.mount.apply(null,arguments)},syncfs(e,t,r){IDBFS.getLocalSet(e,(n,o)=>{if(n)return r(n);IDBFS.getRemoteSet(e,(e,n)=>{if(e)return r(e);IDBFS.reconcile(t?n:o,t?o:n,r)})})},quit(){Object.values(IDBFS.dbs).forEach(e=>e.close()),IDBFS.dbs={}},getDB:(e,t)=>{var r,n=IDBFS.dbs[e];if(n)return t(null,n);try{r=IDBFS.indexedDB().open(e,IDBFS.DB_VERSION)}catch(o){return t(o)}if(!r)return t("Unable to connect to IndexedDB");r.onupgradeneeded=e=>{var t,r=e.target.result,n=e.target.transaction;(t=r.objectStoreNames.contains(IDBFS.DB_STORE_NAME)?n.objectStore(IDBFS.DB_STORE_NAME):r.createObjectStore(IDBFS.DB_STORE_NAME)).indexNames.contains("timestamp")||t.createIndex("timestamp","timestamp",{unique:!1})},r.onsuccess=()=>{n=r.result,IDBFS.dbs[e]=n,t(null,n)},r.onerror=e=>{t(this.error),e.preventDefault()}},getLocalSet(e,t){var r={};function n(e){return"."!==e&&".."!==e}function o(e){return t=>PATH.join2(e,t)}for(var a=FS.readdir(e.mountpoint).filter(n).map(o(e.mountpoint));a.length;){var i,s=a.pop();try{i=FS.stat(s)}catch(u){return t(u)}FS.isDir(i.mode)&&a.push.apply(a,FS.readdir(s).filter(n).map(o(s))),r[s]={timestamp:i.mtime}}return t(null,{type:"local",entries:r})},getRemoteSet:(e,t)=>{var r={};IDBFS.getDB(e.mountpoint,(e,n)=>{if(e)return t(e);try{var o,a,i=n.transaction([IDBFS.DB_STORE_NAME],"readonly");i.onerror=e=>{t(this.error),e.preventDefault()},i.objectStore(IDBFS.DB_STORE_NAME).index("timestamp").openKeyCursor().onsuccess=e=>{var o=e.target.result;if(!o)return t(null,{type:"remote",db:n,entries:r});r[o.primaryKey]={timestamp:o.key},o.continue()}}catch(s){return t(s)}})},loadLocalEntry(e,t){var r,n;try{n=FS.lookupPath(e).node,r=FS.stat(e)}catch(o){return t(o)}return FS.isDir(r.mode)?t(null,{timestamp:r.mtime,mode:r.mode}):FS.isFile(r.mode)?(n.contents=MEMFS.getFileDataAsTypedArray(n),t(null,{timestamp:r.mtime,mode:r.mode,contents:n.contents})):t(Error("node type not supported"))},storeLocalEntry(e,t,r){try{if(FS.isDir(t.mode))FS.mkdirTree(e,t.mode);else{if(!FS.isFile(t.mode))return r(Error("node type not supported"));FS.writeFile(e,t.contents,{canOwn:!0})}FS.chmod(e,t.mode),FS.utime(e,t.timestamp,t.timestamp)}catch(n){return r(n)}r(null)},removeLocalEntry(e,t){try{var r=FS.stat(e);FS.isDir(r.mode)?FS.rmdir(e):FS.isFile(r.mode)&&FS.unlink(e)}catch(n){return t(n)}t(null)},loadRemoteEntry:(e,t,r)=>{var n=e.get(t);n.onsuccess=e=>{r(null,e.target.result)},n.onerror=e=>{r(this.error),e.preventDefault()}},storeRemoteEntry:(e,t,r,n)=>{try{var o=e.put(r,t)}catch(a){n(a);return}o.onsuccess=()=>{n(null)},o.onerror=e=>{n(this.error),e.preventDefault()}},removeRemoteEntry:(e,t,r)=>{var n=e.delete(t);n.onsuccess=()=>{r(null)},n.onerror=e=>{r(this.error),e.preventDefault()}},reconcile:(e,t,r)=>{var n=0,o=[];Object.keys(e.entries).forEach(function(r){var a=e.entries[r],i=t.entries[r];(!i||a.timestamp.getTime()!=i.timestamp.getTime())&&(o.push(r),n++)});var a=[];if(Object.keys(t.entries).forEach(function(t){!e.entries[t]&&(a.push(t),n++)}),!n)return r(null);var i,s=!1,u=("remote"===e.type?e.db:t.db).transaction([IDBFS.DB_STORE_NAME],"readwrite"),l=u.objectStore(IDBFS.DB_STORE_NAME);function m(e){if(e&&!s)return s=!0,r(e)}u.onerror=e=>{m(this.error),e.preventDefault()},u.oncomplete=e=>{s||r(null)},o.sort().forEach(e=>{"local"===t.type?IDBFS.loadRemoteEntry(l,e,(t,r)=>{if(t)return m(t);IDBFS.storeLocalEntry(e,r,m)}):IDBFS.loadLocalEntry(e,(t,r)=>{if(t)return m(t);IDBFS.storeRemoteEntry(l,e,r,m)})}),a.sort().reverse().forEach(e=>{"local"===t.type?IDBFS.removeLocalEntry(e,m):IDBFS.removeRemoteEntry(l,e,m)})}};""")