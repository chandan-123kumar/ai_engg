# ============================================================
# STAGE 8 — Classes & OOP
# ============================================================

# --- Basic class ---
class Dog:
    species = "Canis lupus"     # class variable (shared by all instances)

    def __init__(self, name, age):   # constructor
        self.name = name             # instance variable
        self.age = age

    def bark(self):
        return f"{self.name} says Woof!"

    def __repr__(self):         # unambiguous string (for devs)
        return f"Dog(name={self.name!r}, age={self.age})"

    def __str__(self):          # readable string (for users)
        return f"{self.name} ({self.age} yrs)"


d1 = Dog("Rex", 3)
d2 = Dog("Bella", 5)

print(d1.bark())
print(d2)               # uses __str__
print(repr(d1))         # uses __repr__
print(Dog.species)      # class variable via class
print(d1.species)       # class variable via instance

# --- Inheritance ---
class Animal:
    def __init__(self, name):
        self.name = name

    def speak(self):
        raise NotImplementedError("subclass must implement speak()")

    def __str__(self):
        return f"{self.__class__.__name__}({self.name})"


class Cat(Animal):
    def speak(self):
        return f"{self.name} says Meow!"


class Duck(Animal):
    def speak(self):
        return f"{self.name} says Quack!"


animals = [Cat("Whiskers"), Duck("Donald")]
for animal in animals:
    print(animal.speak())   # polymorphism — same interface, different behavior

# --- super() ---
class GuideDog(Dog):
    def __init__(self, name, age, owner):
        super().__init__(name, age)   # call parent __init__
        self.owner = owner

    def bark(self):
        return f"{super().bark()} (trained)"


g = GuideDog("Buddy", 4, "Alice")
print(g.bark())
print(g.owner)

# --- Properties — controlled attribute access ---
class Circle:
    def __init__(self, radius):
        self._radius = radius       # _ prefix = convention for "private"

    @property
    def radius(self):
        return self._radius

    @radius.setter
    def radius(self, value):
        if value < 0:
            raise ValueError("radius cannot be negative")
        self._radius = value

    @property
    def area(self):
        return 3.14159 * self._radius ** 2


c = Circle(5)
print(c.radius)     # calls getter
print(c.area)       # computed property
c.radius = 10       # calls setter
# c.radius = -1     # raises ValueError

# --- Class & Static methods ---
class MathUtils:
    pi = 3.14159

    @classmethod
    def circle_area(cls, r):    # cls = the class itself
        return cls.pi * r ** 2

    @staticmethod
    def add(a, b):              # no cls or self — just a namespaced function
        return a + b


print(MathUtils.circle_area(5))
print(MathUtils.add(3, 4))

# --- Dunder (magic) methods ---
class Vector:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __add__(self, other):       # v1 + v2
        return Vector(self.x + other.x, self.y + other.y)

    def __len__(self):              # len(v)
        return int((self.x**2 + self.y**2) ** 0.5)

    def __repr__(self):
        return f"Vector({self.x}, {self.y})"


v1 = Vector(1, 2)
v2 = Vector(3, 4)
print(v1 + v2)      # Vector(4, 6)
print(len(v2))      # 5

# ============================================================
# TASK:
#   Create a class `BankAccount` with:
#   - __init__(owner, balance=0)
#   - deposit(amount) method
#   - withdraw(amount) — raise ValueError if insufficient funds
#   - __str__ returning "owner: $balance"
#   Test it: deposit 500, withdraw 200, try withdrawing 400 (should error)
# ============================================================
class BankAccount:
    def __init__(self, owner, balance=0):
        self._owner = owner
        self._balance = balance
    def deposit(self, amount):
        self._balance += amount
    def withdraw(self, amount):
        if self._balance < amount:
            raise  ValueError("Insufficient amountr")
        self._balance -= amount
    def __str__(self):
        return f"your balance is {self._balance}"  
        
acc = BankAccount("Alice")
acc.deposit(500)
acc.withdraw(200)
print(acc)