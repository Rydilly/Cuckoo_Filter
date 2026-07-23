import mmh3
import random
import math

"""
use xor to compare bits and swap back and forth 
5 ^ 3 = 6
5 ^ 6 = 3
...
"""

"""
the odds i bucket cell has the same fingerprint I'm putting in is 2^(f)ingerprint_bits-1 (disclude 0 because z xor 0==z)
so the odds of not finding our fingerpint in 2 buckets is (1-1/(2^(f-1))^((b)ucket_size*2) 
so the odds of finding our fingerprint in 2 buckest is 1-(1-1/(2^(f-1))^(2b) or about .031 for b=4 and f=8
if a fraction of the bucket slots are filled 1/2^(f-1) * a with a being the load factor (x/8 filled slots in both buckets) meaning linear decline as the ratio of buckets decreases. 
the full equation approximates to 2b/2^f = z (false positive rate)
if i solve for f to find how long my finger_print bits need to be to avoid a certain percentage of false positives
z/2b=2^f-> f = ln(2b/z)/ln2

if I solve for size from capacity I know (s)ize = (c)apacity/((b)ucket_size*.95) #.95 is the load limit to avoid failed adds in most cases. (1 slot is 50% and 8 is 98%) 
so capacity is (95%b)s. no pun intended


my false positive rate was .004 after adding 500 items and checking for 10000 items
the reason my rate is so much lower then what i calculated is because my tables size is 1024 * 4 = 4096slots and my calculation is for worst case when both buckets are full

I've notice past around .8 cap I run into issues with finding less items then i added. I'm assuming this is due to insertions fails which seems high for a alg that loops 500 times every time it cant find a avalible slot

I had a bug where my fingerprint to hash seeds were 0 and 1 for 2 seperate instances. 
"""


class cuckoo_hash:
    def __init__(self, capacity = 1024,fpr = .01):
        self.bucket_size = 4
        self.size = math.ceil(capacity/(self.bucket_size*.95))
        self.finger_byte_size = math.ceil(math.log((2*self.bucket_size)/fpr)/math.log(2))
        self.finger_byte_size = (self.finger_byte_size+7)//8
        self.finger_max = (1<<self.finger_byte_size*8)-1#for getting finger prints from keys larger then this with and
        self.buffer = bytearray(self.bucket_size*self.size*self.finger_byte_size)
        

    def fingerprint_and_idxs(self, item):
        match item:
            case int():
                item_bytes = item.to_bytes(8,"big")
            case str():
                item_bytes = item.encode()
            case _:
                raise TypeError("item type not yet implemented")
            
        finger_print = mmh3.hash(item_bytes, seed = 42, signed = False) & self.finger_max
        if finger_print ==0:
            finger_print=1

        idx1 = (mmh3.hash(item_bytes, seed = 0, signed = False))%self.size
        idx2 = (idx1 ^ mmh3.hash(finger_print.to_bytes(self.finger_byte_size, "big"), seed = 1, signed = False))%self.size

        return finger_print, idx1, idx2
    
    def add(self, item):
        finger_print, idx1, idx2 = self.fingerprint_and_idxs(item)
        for i in range(self.bucket_size): 
            if self._read_slot(idx1, i) ==0:#is compares address rather then underlying val making it faster
                self._write_slot(idx1, i, finger_print)
                return True
            elif self._read_slot(idx2, i)==0 :
                self._write_slot(idx2, i, finger_print)
                return True
        current_i = random.choice([idx1,idx2])

        for i in range(500):
            which_slot = random.randint(0,self.bucket_size-1)
            
            next = self._read_slot(current_i, which_slot)
            self._write_slot(current_i, which_slot, finger_print)
            finger_print = next
             
            current_i = (current_i ^ mmh3.hash(finger_print.to_bytes(8,"big"),seed =1, signed = False))%self.size

            for i in range(self.bucket_size):
                if self._read_slot(current_i, i) == 0:
                    self._write_slot(current_i, i, finger_print)
                    return True
                
        return False

    def contains(self, item):
        finger_print, idx1, idx2 = self.fingerprint_and_idxs(item)
        for i in range(self.bucket_size):
            if self._read_slot(idx1, i)== finger_print:
                return True
            if self._read_slot(idx2,i)==finger_print:
                return True
        return False
    
    def delete(self, item):
        fingerprint, idx1, idx2 = self.fingerprint_and_idxs(item)
        
        for i in range(self.bucket_size):#only 1 finger print stored so we can stop when 1 is found
            if self._read_slot(idx1, i)==fingerprint:
                self._write_slot(idx1, i, 0)
                return True
            if self._read_slot(idx2,i)==fingerprint:
                self._write_slot(idx2, i, 0)
                return True            
        return False

    def _read_slot(self, bucket_idx, slot_idx):#needed to implement this so the machine knows how many bytes to write to.
        start = (bucket_idx*self.bucket_size+slot_idx)*self.finger_byte_size
        end = start+self.finger_byte_size
        return int.from_bytes(self.buffer[start:end], "big")
    
    def _write_slot(self, bucket_idx, slot_idx, val):
        start = (bucket_idx*self.bucket_size+slot_idx)*self.finger_byte_size
        end = start+self.finger_byte_size
        self.buffer[start:end]= val.to_bytes(self.finger_byte_size, "big")
        
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

    n = 3900#items added
    n_count = 0
    m = 50000#items checked
    pos = 0
    neg = 0

    t = cuckoo_hash(50000)
    for i in range(n):
        if t.add(i):
            n_count+=1
    for i in range(m):
        if t.contains(i):
            pos+=1
        else:
            neg+=1
    
    print("items found in cuckoo hash: ", pos, ", items added: ", n_count)#note this does not calc for elements that never got hashed
    print("items not found: ", neg, ", expected: ", m-n_count)
    print("false positive ratio: ", (pos-n)/(m-n))


    n = cuckoo_hash()
    n_attempted = 3900
    n_actual = 0
    for i in range(n_attempted):
        if n.add(i):
            n_actual += 1
    print(f"attempted: {n_attempted}, actual: {n_actual}")

    print("\n\n")

    #ai made test
    cf = cuckoo_hash(capacity=50000, fpr=0.01)
    inserted = [i for i in range(50000) if cf.add(i)]
    print(f"inserted: {len(inserted)} / 50000")

    trials = 100000
    fp = sum(cf.contains(i) for i in range(1000000, 1000000 + trials))
    print(f"FPR: {fp/trials:.5f} (target: 0.01)")


