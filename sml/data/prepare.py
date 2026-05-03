with open("data/input.txt", "r", encoding="utf-8") as f:
    text = f.read()

# 90% train, 10% validation
n = int(0.9 * len(text))
train_text = text[:n]
val_text   = text[n:]

with open("data/train.txt", "w", encoding="utf-8") as f:
    f.write(train_text)

with open("data/val.txt", "w", encoding="utf-8") as f:
    f.write(val_text)

print(f"Total characters : {len(text):,}")
print(f"Train characters : {len(train_text):,}  ({len(train_text)/len(text)*100:.1f}%)")
print(f"Val characters   : {len(val_text):,}   ({len(val_text)/len(text)*100:.1f}%)")