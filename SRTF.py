import simpy
#import random
import numpy.random as random

''' ------------------------ '''
''' Parameters               '''
''' ------------------------ '''
MAXSIMTIME = 3
VERBOSE = True
LAMBDA = 5.0
MU = 8.0
POPULATION = 50000000
SERVICE_DISCIPLINE = 'SRTF'
LOGGED = True

''' ------------------------ '''
''' DES model                '''
''' ------------------------ '''
class Job:
    def __init__(self, name, arrtime, duration):
        self.name = name
        self.arrtime = arrtime
        self.duration = duration
        self.RemandTime = duration
    def __str__(self):
        return '%s at %d, length %d' %(self.name, self.arrtime, self.duration)

def SRTF( job ):
    return job.RemandTime

''' A server
 - env: SimPy environment
 - strat: - FIFO: First In First Out
          - SJF : Shortest Job First
'''
class Server:
    def __init__(self, env, strat = 'SRTF'):
        self.env = env
        self.strat = strat
        self.Jobs = list(())
        self.serversleeping = None
        ''' statistics '''
        self.waitingTime = 0
        self.idleTime = 0
        self.jobsDone = 0
        self.Jobdoing = Job('Job 0' , 0 , 0)
        ''' register a new server process '''
        env.process( self.serve() )

    def serve(self):
        while True:
            ''' do nothing, just change server to idle
              and then yield a wait event which takes infinite time
            '''
            if len( self.Jobs ) == 0 :
                self.serversleeping = env.process( self.waiting( self.env ))
                t1 = self.env.now
                yield self.serversleeping
                ''' accumulate the server idle time'''
                self.idleTime += self.env.now - t1
            else:
                ''' get the first job to be served'''
                self.Jobs.sort( key = SRTF )
                self.jobDoing = self.Jobs.pop( 0 )
                print('%s in sever at %.2f'%(self.jobDoing.name,self.env.now))
                #if LOGGED:
                #    qlog.write( '%.4f\t%d\t%d\n'
                #        % (self.env.now, 1 if len(self.Jobs)>0 else 0, len(self.Jobs)) )

                ''' sum up the waiting time'''
                if self.Jobdoing.RemandTime == 0:
                    print('%s is done at %.2f' % (self.Jobdoing.name, self.env.now))
                    self.waitingTime += self.env.now - self.jobDoing.arrtime
                    self.jobsDone += 1
                ''' yield an event for the job finish'''
                yield self.env.timeout( self.jobDoing.duration )
                ''' sum up the jobs done '''

    def waiting(self, env):
        try:
            if VERBOSE:
                print( 'Server is idle at %.2f' % self.env.now )
            yield self.env.timeout( MAXSIMTIME )
        except simpy.Interrupt as i:
            if VERBOSE:
                 print('Server waken up and works at %.2f' % self.env.now )

class JobGenerator:
    def __init__(self, env, server, nrjobs = 10000000, lam = 5, mu = 8):
        self.server = server
        self.nrjobs = nrjobs
        self.interarrivaltime = 1/lam;
        self.servicetime = 1/mu;
        env.process( self.generatejobs(env) )

    def generatejobs(self, env):
        i = 1
        while True:
            '''yield an event for new job arrival'''
            job_interarrival = random.exponential( self.interarrivaltime )
            yield env.timeout( job_interarrival )

            ''' generate service time and add job to the list'''
            job_duration = random.exponential( self.servicetime )
            t_NewArr = env.now
            self.server.Jobs.append( Job('Job %s' %i, env.now, job_duration) )
            if i > 1 and self.server.Jobdoing.RemandTime > 0:
                self.server.Jobdoing.RemandTime = self.server.Jobdoing.RemandTime - ( env.now - self.server.Jobdoing.arrtime )
                if self.server.Jobdoing.RemandTime>0:
                    self.server.Jobdoing.arrtime=env.now
                    self.server.Jobs.append(self.server.Jobdoing)

            if VERBOSE:
                print( 'job %d: t = %.2f, l = %.2f, dt = %.2f'
                    %( i, env.now, job_duration, job_interarrival ) )
            i += 1

            ''' if server is idle, wake it up'''
            if not self.server.serversleeping.triggered:
                self.server.serversleeping.interrupt( 'Wake up, please.' )

''' open a log file '''
if LOGGED:
    qlog = open( 'mm1-l%d-m%d.csv' % (LAMBDA,MU), 'w' )
    qlog.write( '0\t0\t0\n' )

''' start SimPy environment '''
env = simpy.Environment()
MyServer = Server( env, SERVICE_DISCIPLINE )
MyJobGenerator = JobGenerator( env, MyServer, POPULATION, LAMBDA, MU )

''' start simulation '''
env.run( until = MAXSIMTIME )

''' close log file '''
if LOGGED:
    qlog.close()

''' print statistics '''
RHO = LAMBDA/MU
print( 'Arrivals               : %d' % (MyServer.jobsDone) )
print( 'Utilization            : %.2f/%.2f'
    % (1.0-MyServer.idleTime/MAXSIMTIME, RHO) )
print( 'Mean waiting time      : %.2f/%.2f'
    % (MyServer.waitingTime/MyServer.jobsDone, RHO**2/((1-RHO)*LAMBDA) ) )


