#!/usr/bin/env python3
import sys

class Condition:
    def __init__(self):
        self.current_state_ = 0
        self.previous_state_ = -1
        self.input_values_ = []
        self.state_2_cnt_ = dict()
        self.state_change_2_cnt_ = dict()

    def update_values(self, v0, v1, v2, v3, v4, v5, v6):
        self.previous_state_ = self.current_state_
        self.input_values_ = [v0, v1, v2, v3, v4, v5, v6]

        self.current_state_ = 0
        bit_index = 0
        for i in range(6):
            for j in range(i + 1, 7):
                if self.input_values_[i] > self.input_values_[j]:
                    self.current_state_ |= 1 << bit_index
                bit_index += 1
        if self.current_state_ not in self.state_2_cnt_:
            self.state_2_cnt_[self.current_state_] = 0

        if self.previous_state_ == -1:
            self.previous_state_ = self.current_state_
        self.state_2_cnt_[self.current_state_] +=1
        if self.previous_state_ != self.current_state_:
            state_change = f'{self.previous_state_}_{self.current_state_}'
            if state_change not in self.state_change_2_cnt_:
                self.state_change_2_cnt_[state_change] = 0
            self.state_change_2_cnt_[state_change] += 1
        pass


    def check_cross(self):
        crossed_info = []
        if self.current_state_ == -1 or self.previous_state_ == -1:
            return crossed_info
        bit_index = 0
        for i in range(6):
            for j in range(i + 1, 7):
                current_relation = (self.current_state_ >> bit_index) & 1
                previous_relation = (self.previous_state_ >> bit_index) & 1
                if current_relation != previous_relation:
                    vi, vj = self.input_values_[i], self.input_values_[j]
                    relation_change = "crossed above" if current_relation == 1 else "crossed below"
                    crossed_info.append(f"v{i} and v{j} ({vi} and {vj}): {relation_change}")
                bit_index += 1
        return crossed_info

    def get_binary_values(self):
        current_bin = bin(self.current_state_)[2:].zfill(21)
        previous_bin = bin(self.previous_state_)[2:].zfill(21)
        return current_bin, previous_bin
    
    def describe_relations(self):
        if self.current_state_ == -1:
            return "No relations defined"
        relations = []
        bit_index = 0
        for i in range(6):
            for j in range(i + 1, 7):
                relation = "≤" if (self.current_state_ >> bit_index) & 1 == 0 else ">"
                relations.append(f"v{i} {relation} v{j}")
                bit_index += 1
        return ", ".join(relations)

if __name__ == '__main__':
    c = Condition()
    c.update_values(192.4, 184,185,187,186,190.2,210)
    c.update_values(243.4, 184,185,191,186,190.2,210)
    print(f"{c.check_cross()}")
    print(f"{c.get_binary_values()}")
    print(f"{c.describe_relations()}")
    sys.exit(0)
