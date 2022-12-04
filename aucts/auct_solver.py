import sys
sys.path.append('../')

import msat_runner
import wcnf

MAXSAT_SOLVER = ''
INPUT_FILE = ''
MIN_WIN_BIDS = True



class CombinatorialAuction:
    def __init__(self, agents, goods, bids):
        self.agents = agents
        self.goods = goods
        self.bids = bids


    def solve(self):
        """Solves the combinatorial auction problem.

        :return: A solution (list of winning bids and the total benefit).
        """

        formula = self.toWPMS()
        # Create a MaxSAT solver instance
        solver = msat_runner.MaxSATRunner(MAXSAT_SOLVER)
        _, model = solver.solve(formula)
        # Check if the problem is satisfiable.
        winningBids = [bid[0] for bid in self.bids.items() if bid[0] in model]
        if len(winningBids) == 0:
            print('Unsatisfiable')
            return
        # Calculate and print the total benefit.
        print('\nBenefit: ' + str(sum([bid[1].price for bid in self.bids.items() if bid[0] in model])))
        # Print the winning bids.
        for bid in model:
            if bid < 0:
                continue
            bidObject = self.bids[bid]
            print(str(bidObject.agent) + ': ' + ','.join(bidObject.goods) + ' (Price ' + str(bidObject.price) + ')')

        self.checkSolution(winningBids)


    def toWPMS(self):
        """Converts the combinatorial auction object to a Weighted Partial MaxSAT formula.

        :return: The Weighted Partial MaxSAT formula.
        """

        formula = wcnf.WCNFFormula()
        # For every bid, add a soft clause with the bid's weight.
        for bid in self.bids.items():
            literal = bid[0]
            weight = bid[1].price
            formula.new_var()
            formula.add_clause([literal], weight)
        # For every pair of bids that are not compatible, add a hard clause.
        for bid1 in self.bids.items():
            for bid2 in self.bids.items():
                if bid1[0] != bid2[0] and not bid1[1].is_compatible(bid2[1]) and bid1[0] < bid2[0]:
                    formula.new_var()
                    formula.add_clause([-bid1[0], -bid2[0]])

        if MIN_WIN_BIDS:
            self.addMinWinBidsClauses(formula)

        return formula


    def addMinWinBidsClauses(self, formula):
        """Adds the clauses that guarantee that each agent wins at least one bid.

        :param formula: The formula to which the additional clauses will be added.
        :type formula: wcnf.WCNFFormula
        """

        for agent in self.agents:
            agent_bids = [bid[0] for bid in self.bids.items() if bid[1].agent == agent]
            formula.new_var()
            formula.add_clause(agent_bids)


    def checkSolution(self, winningBids):
        """Checks if the given solution is valid.

        :param winningBids: The list of winning bids.
        :type winningBids: list
        """

        # Search for conflicting bids.
        for bid in winningBids:
            bidObject = self.bids[bid]
            for otherBid in winningBids:
                if bid < otherBid:
                    otherBidObject = self.bids[otherBid]
                    if not bidObject.is_compatible(otherBidObject):
                        print('Invalid Solution')
                        return

        # Check if each agent wins at least one bid.
        if MIN_WIN_BIDS:
            for agent in self.agents:
                agent_bids = [bid for bid in winningBids if self.bids[bid].agent == agent]
                if len(agent_bids) == 0:
                    print('Invalid Solution')
                    return

        print('Valid Solution')



class Bid:
    def __init__(self, agent, goods, price):
        self.agent = agent
        self.goods = goods
        self.price = price


    def is_compatible(self, other):
        """Returns true if this bid is compatible with the other bid.

        :param other: The other bid.
        :type other: Bid
        :return: True if the bids are compatible, False otherwise.
        """

        self_goods = set(self.goods)
        other_goods = set(other.goods)
        return self_goods.isdisjoint(other_goods)


def parse_args():
    """Parse command line arguments."""

    global MAXSAT_SOLVER, INPUT_FILE, MIN_WIN_BIDS
    MAXSAT_SOLVER = sys.argv[1]
    INPUT_FILE = sys.argv[2]
    if len(sys.argv) > 3:
        if sys.argv[3] == '--no-min-win-bids':
            MIN_WIN_BIDS = False
        else:
            print('Unknown flag: ' + sys.argv[3])
            sys.exit(1)


def parse_file(filename):
    """Parse input file and create a combinatorial auction object."""

    try:
        file = open(filename, 'r')
    except FileNotFoundError:
        print('File not found: ' + filename)
        sys.exit(1)

    agents = file.readline().strip().split(' ')[1:]
    goods = file.readline().strip().split(' ')[1:]
    bids = dict()
    dictIndex = 1
    for line in file:
        agent = line.strip().split(' ')[0]
        good = line.strip().split(' ')[1:-1]
        price = line.strip().split(' ')[-1]
        bids.update({dictIndex: Bid(agent, good, int(price))})
        dictIndex += 1

    return CombinatorialAuction(agents, goods, bids)


def main():
    if len(sys.argv) < 3:
        print('Usage: python3 auct_solver.py <maxsat_solver> <input_file> [--no-min-win-bids]')
        sys.exit(1)
    parse_args()
    CombinatorialAuctionInstance = parse_file(INPUT_FILE)
    CombinatorialAuctionInstance.solve()


if __name__ == '__main__':
    main()