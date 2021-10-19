    def get_variable_cost(self, pM):
        
        time = pM.time
        ckey = self.__str__()
        zeros = np.zeros(len(time))

        charging = getattr(pM, ckey + "_Pneg", zeros)
        discharging = getattr(pM, ckey + "_Ppos", zeros)
        
        # note: variable_income should be negative!
        income = sum(charging[t] * self.variable_income for t in time)
        cost = sum(discharging[t] * self.variable_cost for t in time)

        return cost + income