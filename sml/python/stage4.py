# ============================================================
# STAGE 4 — Lists, Tuples, Sets, Dictionaries
# ============================================================

# ---- LIST — ordered, mutable, allows duplicates ----
fruits = ["apple", "banana", "cherry"]

fruits.append("mango")        # add to end
fruits.insert(1, "blueberry") # insert at index
fruits.remove("banana")       # remove by value
popped = fruits.pop()         # remove & return last item
print(fruits)
print(popped)

fruits.sort()                 # sort in place
print(fruits)
print(sorted(fruits, reverse=True))  # returns new sorted list

print(len(fruits))
print(fruits[0], fruits[-1])

# Slicing works same as strings
nums = [0, 1, 2, 3, 4, 5]
print(nums[1:4])    # [1, 2, 3]
print(nums[::-1])   # reversed

# ---- TUPLE — ordered, IMMUTABLE, allows duplicates ----
point = (3, 7)
x, y = point        # unpacking
print(x, y)

rgb = (255, 128, 0)
# rgb[0] = 100      # TypeError — can't modify

# Use tuples for fixed data (coordinates, DB rows, config)
# Tuples are faster than lists and can be dict keys

# ---- SET — unordered, mutable, NO duplicates ----
s = {1, 2, 3, 3, 2}
print(s)             # {1, 2, 3} — duplicates removed

s.add(4)
s.discard(10)        # safe remove — no error if missing

a = {1, 2, 3, 4}
b = {3, 4, 5, 6}
print(a | b)         # union        {1,2,3,4,5,6}
print(a & b)         # intersection {3,4}
print(a - b)         # difference   {1,2}
print(a ^ b)         # symmetric diff {1,2,5,6}

# ---- DICT — key-value pairs, ordered (3.7+), mutable ----
person = {
    "name": "Alice",
    "age": 30,
    "skills": ["Python", "SQL"]
}

print(person["name"])               # Alice
print(person.get("salary", 0))      # 0 — safe get with default

person["age"] = 31                  # update
person["city"] = "NYC"              # add new key
del person["city"]                  # delete key

print(person.keys())
print(person.values())
print(person.items())               # [(key, val), ...]

# Looping a dict
for key, val in person.items():
    print(f"{key}: {val}")

# Merging dicts (Python 3.9+)
defaults = {"theme": "dark", "lang": "en"}
user_prefs = {"lang": "fr", "font": "mono"}
merged = defaults | user_prefs      # user_prefs wins on conflict
print(merged)

# ---- Nested structures ----
users = [
    {"id": 1, "name": "Alice"},
    {"id": 2, "name": "Bob"},
]
print(users[1]["name"])   # Bob

# ============================================================
# TASK:
#   1. Create a list of 5 numbers with duplicates
#   2. Convert to a set to remove duplicates
#   3. Store each number as a key in a dict with its square as value
#      e.g. {2: 4, 3: 9, ...}
#   4. Print the dict
# ============================================================
dict = {}
for i in range(5):
    print(i)