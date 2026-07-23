import mmh3
from bitarray import bitarray
import random

"""
use xor to compare bits and swap back and forth 
5 ^ 3 = 6
5 ^ 6 = 3
...
"""

"""
the odds i bucket cell has the same fingerprint I'm putting in is 2^(f)ingerprint_bits-1 (disclude 0 because z xor 0==z)
so the odds of not finding our fingerpint in 2 buckets is (1-1/(2^f-1))^((b)ucket_size*2) 
so the odds of finding our fingerprint in 2 buckest is 1-(1-1/(2^f-1))^(2b) or about .031 for b=4 and f=8

my false positive rate was .004 after adding 500 items and checking for 10000 items
the reason my rate is so much lower then what i calculated is because my tables size is 1024 * 4 = 4096slots and my calculation is for worst case when both buckets are full

I've notice past around .8 cap I run into issues with finding less items then i added. I'm assuming this is due to insertions fails which seems high for a alg that loops 500 times every time it cant find a avalible slot

I had a bug where my fingerprint to hash seeds were 0 and 1 for 2 seperate instances. 
"""


class cuckoo_hash:
    def __init__(self, size = 1024, bucket_size = 4):
        self.buffer = [[None]*bucket_size for i in range(size)]
        self.size = size
        self.bucket_size = bucket_size

    def fingerprint_and_idxs(self, item):
        match item:
            case int():
                item_bytes = item.to_bytes(8,"big")
            case str():
                item_bytes = item.encode()
            case _:
                raise TypeError("item type not yet implemented")
            
        finger_print = mmh3.hash(item_bytes, seed = 42, signed = False) & 0xFF
        if finger_print ==0:
            finger_print=1

        idx1 = (mmh3.hash(item_bytes, seed = 0, signed = False))%self.size
        idx2 = (idx1 ^ mmh3.hash(finger_print.to_bytes(1, "big"), seed = 1, signed = False))%self.size

        return finger_print, idx1, idx2
    
    def add(self, item):
        finger_print, idx1, idx2 = self.fingerprint_and_idxs(item)
        for i in range(self.bucket_size): 
            if self.buffer[idx1][i] is None:#is compares address rather then underlying val making it faster
                self.buffer[idx1][i]=finger_print
                return True
            elif self.buffer[idx2][i] is None:
                self.buffer[idx2][i]=finger_print
                return True
        current_i = random.choice([idx1,idx2])

        for i in range(500):
            which_slot = random.randint(0,self.bucket_size-1)
            
            next = self.buffer[current_i][which_slot]
            self.buffer[current_i][which_slot]=finger_print
            finger_print = next
             
            current_i = (current_i ^ mmh3.hash(finger_print.to_bytes(1,"big"),seed =1, signed = False))%self.size

            for i in range(self.bucket_size):
                if self.buffer[current_i][i] is None:
                    self.buffer[current_i][i]=finger_print
                    return True
                
        return False

    def contains(self, item):
        finger_print, idx1, idx2 = self.fingerprint_and_idxs(item)
        return finger_print in self.buffer[idx1] or finger_print in self.buffer[idx2]
    
    def delete(self, item):
        fingerprint, idx1, idx2 = self.fingerprint_and_idxs(item)
        
        for i in range(self.bucket_size):#only 1 finger print stored so we can stop when 1 is found
            if self.buffer[idx1][i]==fingerprint:
                self.buffer[idx1][i]=None
                return True
            if self.buffer[idx2][i]==fingerprint:
                self.buffer[idx2][i]=None
                return True            
        return False

        
if __name__ == "__main__":
    c = cuckoo_hash()
    for i in range(100):
        c.add(i)
    print(all(c.contains(i) for i in range(100)))
    print(c.contains(999999))

    for i in range(50):
        c.delete(i)
    print(sum(c.contains(i) for i in range(50)))
    print(sum(c.contains(i) for i in range(50, 100)))

    n = 3200#items added
    m = 10000#items checked
    pos = 0
    neg = 0

    t = cuckoo_hash()
    for i in range(n):
        t.add(i)
    for i in range(m):
        if t.contains(i):
            pos+=1
        else:
            neg+=1
    
    print("items found in cuckoo hash: ", pos, ", items added: ", n)#note this does not calc for elements that never got hashed
    print("items not found: ", neg, ", expected: ", m-n)
    print("false positive ratio: ", (pos-n)/(m-n))


    n = cuckoo_hash()
    n_attempted = 3900
    n_actual = 0
    for i in range(n_attempted):
        if n.add(i):
            n_actual += 1
    print(f"attempted: {n_attempted}, actual: {n_actual}")


