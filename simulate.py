'''
Polling places

YOUR NAME(s) HERE

Main file for polling place simulation
'''

import sys
import random
import queue
import click
import util



class Voter(object):
    '''
    Voter class
    '''
    def __init__(self, arrival_time, voting_duration,
                start_time=None, end_time=None):
        '''
        Constructor for the Voter class

        Input:
            arrival_time: (int) Minute of arrival
            voting_duration: (float) Time it takes for a voter to vote
            start_time: (int) Time a voter gets in the booth
            end_time: (int) Time a voter is done with voting
        '''
        self.arrival_time = arrival_time
        self.voting_duration = voting_duration
        self.start_time = start_time
        self.end_time = end_time

    def update_startend_times(self, start_time):
        '''
        Updates the start and departure time of the voter by adding
        voting duration.

        Input:
            start_time: (int) Time a voter gets in the booth
        '''
        self.start_time = start_time
        self.end_time = self.start_time + self.voting_duration


class Precinct(object):
    '''
    Precinct class
    '''

    def __init__(self, name, hours_open, max_num_voters, num_booths,
                arrival_rate, voting_duration_rate):
        '''
        Constructor for the Precinct class

        Input:
            name: (str) Name of the precinct
            hours_open: (int) Hours the precinct will remain open
            max_num_voters: (int) Number of voters in the precinct
            num_booths: (int) Number of voting booths in the precinct
            arrival_rate: (float) Rate at which voters arrive
            voting_duration_rate: (float) Lambda for voting duration
        '''

        self.name = name
        self.minutes_open = hours_open * 60
        self.max_num_voters = max_num_voters
        self.num_booths = num_booths
        self.arrival_rate = arrival_rate
        self.voting_duration_rate = voting_duration_rate


    def simulate(self, percent_straight_ticket, straight_ticket_duration, seed):
        '''
        Simulate a day of voting

        Input:
            percent_straight_ticket: (float) Percentage of straight-ticket
                                     voters as a decimal between 0 and 1
                                     (inclusive)
            straight_ticket_duration: (float) Voting duration for
                                      straight-ticket voters
            seed: (int) Random seed to use in the simulation

        Output:
            List of voters who voted in the precinct
        '''
        voters = []
        random.seed(seed)
        cur_time = 0

        while len(voters) + 1 <= self.max_num_voters:
            if random.random() <= percent_straight_ticket:
                voting_duration = straight_ticket_duration
            else:
                voting_duration = random.expovariate(self.voting_duration_rate)
            gap = random.expovariate(self.arrival_rate)
            cur_time += gap
            if cur_time  > self.minutes_open:
                break
            voter = Voter(cur_time, voting_duration)
            voters.append(voter)

        booth = VotingBooths(self.num_booths)
        for voter in voters:
            if not booth.full():
                voter.update_startend_times(voter.arrival_time)
                booth.put(voter.end_time)
            else:
                voter.update_startend_times(max(voter.arrival_time,
                                                booth.get()))
                booth.put(voter.end_time)

        return voters


class VotingBooths(object):
    '''
    VotingBooths class
    '''

    def __init__(self, num_booths):
        '''
        Constructor for the VotingBooths class via a PriorityQueue

        Input:
            num_booths: (int) Number of voting booths in the precinct
        '''
        self.num_booths = num_booths
        self.booths = queue.PriorityQueue(num_booths)

    def put(self, priority):
        '''
        Adds a voter's departure time to the queue

        Input:
            priority: (float) voter's departure time
        '''
        self.booths.put(priority)

    def get(self):
        '''
        Removes the voter who departures the first from the queue

        Output: (float) the departure time that is removed from queue
        '''
        return self.booths.get()

    def full(self):
        '''
        Checks if all the voting booths are full (if queue is at capacity)

        Output: (boolean) True if queue is full, False if it is not
        '''
        return self.booths.full()


def find_avg_wait_time(precinct, percent_straight_ticket,
                       ntrials, initial_seed=0):
    '''
    Simulates a precinct multiple times with a given percentage of
    straight-ticket voters. For each simulation, computes the average
    waiting time of the voters, and returns the median of those average
    waiting times.

    Input:
        precinct: (dictionary) A precinct dictionary
        percent_straight_ticket: (float) Percentage straight-ticket voters
        ntrials: (int) The number of trials to run
        initial_seed: (int) Initial seed for random number generator

    Output:
        The median of the average waiting times returned by simulating
        the precinct 'ntrials' times.
    '''

    p = Precinct(precinct['name'], precinct['hours_open'],
                 precinct['num_voters'], precinct['num_booths'],
                 precinct['arrival_rate'], precinct['voting_duration_rate'])

    seed = initial_seed
    avg_wait_times = []

    for _ in range(ntrials):
        voters = p.simulate(percent_straight_ticket,
                            precinct['straight_ticket_duration'], seed)
        wait_times = []
        for voter in voters:
            wait_time = voter.start_time - voter.arrival_time
            wait_times.append(wait_time)
        avg_wait_times.append(sum(wait_times) / len(wait_times))
        seed += 1

    avg_wait_times.sort()

    return avg_wait_times[ntrials // 2]


def find_percent_split_ticket(precinct, target_wait_time, ntrials, seed=0):
    '''
    Finds the percentage of split-ticket voters needed to bound
    the (average) waiting time.

    Input:
        precinct: (dictionary) A precinct dictionary
        target_wait_time: (float) The minimum waiting time
        ntrials: (int) The number of trials to run when computing
                 the average waiting time
        seed: (int) A random seed

    Output:
        A tuple (percent_split_ticket, waiting_time) where:
        - percent_split_ticket: (float) The percentage of split-ticket
                                voters that ensures the average waiting time
                                is above target_waiting_time
        - waiting_time: (float) The actual average waiting time with that
                        percentage of split-ticket voters

        If the target waiting time is infeasible, returns (0, None)
    '''
    for split, straight in enumerate(range(11)[::-1]):
        avg_wait = find_avg_wait_time(precinct, straight / 10, ntrials, seed)
        if avg_wait > target_wait_time:
            return(split / 10, avg_wait)
        if split == 10:
            return(1, None)


# DO NOT REMOVE THESE LINES OF CODE
# pylint: disable-msg= invalid-name, len-as-condition, too-many-locals
# pylint: disable-msg= missing-docstring, too-many-branches
# pylint: disable-msg= line-too-long
@click.command(name="simulate")
@click.argument('precincts_file', type=click.Path(exists=True))
@click.option('--target-wait-time', type=float)
@click.option('--print-voters', is_flag=True)
def cmd(precincts_file, target_wait_time, print_voters):
    precincts, seed = util.load_precincts(precincts_file)

    if target_wait_time is None:
        voters = {}
        for p in precincts:
            precinct = Precinct(p["name"],
                                p["hours_open"],
                                p["num_voters"],
                                p["num_booths"],
                                p["arrival_rate"],
                                p["voting_duration_rate"])
            voters[p["name"]] = precinct.simulate(p["percent_straight_ticket"], p["straight_ticket_duration"], seed)
        print()
        if print_voters:
            for p in voters:
                print("PRECINCT '{}'".format(p))
                util.print_voters(voters[p])
                print()
        else:
            for p in precincts:
                pname = p["name"]
                if pname not in voters:
                    print("ERROR: Precinct file specified a '{}' precinct".format(pname))
                    print("       But simulate_election_day returned no such precinct")
                    print()
                    sys.exit(-1)
                pvoters = voters[pname]
                if len(pvoters) == 0:
                    print("Precinct '{}': No voters voted.".format(pname))
                else:
                    pl = "s" if len(pvoters) > 1 else ""
                    closing = p["hours_open"]*60.
                    last_depart = pvoters[-1].departure_time
                    avg_wt = sum([v.start_time - v.arrival_time for v in pvoters]) / len(pvoters)
                    print("PRECINCT '{}'".format(pname))
                    print("- {} voter{} voted.".format(len(pvoters), pl))
                    msg = "- Polls closed at {} and last voter departed at {:.2f}."
                    print(msg.format(closing, last_depart))
                    print("- Avg wait time: {:.2f}".format(avg_wt))
                    print()
    else:
        precinct = precincts[0]

        percent, avg_wt = find_percent_split_ticket(precinct, target_wait_time, 20, seed)

        if percent == 0:
            msg = "Waiting times are always below {:.2f}"
            msg += " in precinct '{}'"
            print(msg.format(target_wait_time, precinct["name"]))
        else:
            msg = "Precinct '{}' exceeds average waiting time"
            msg += " of {:.2f} with {} percent split-ticket voters"
            print(msg.format(precinct["name"], avg_wt, percent*100))


if __name__ == "__main__":
    cmd() # pylint: disable=no-value-for-parameter
