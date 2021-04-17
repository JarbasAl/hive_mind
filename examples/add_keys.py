from jarbas_hive_mind.database import ClientDatabase

name = "JarbasTestClient"   # placeholder, human readable string, unused
key = "RESISTENCEisFUTILE"   # pre shared access key
crypto_key = "resistanceISfutile"   # pre shared encryption key (optional)
mail = "jarbasaai@mailfence.com"  # placeholder, unused


with ClientDatabase() as db:
    db.add_client(name, mail, key, crypto_key=crypto_key)


name = "AutoCrypto"
key = "HerpDerpHerpDurr"  # pre shared key
with ClientDatabase() as db:
    db.add_client(name, mail, key)
