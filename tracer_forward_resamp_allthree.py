from pyDOE import lhs
import sys
sys.path.append(r"C:\Users\shikhar\PycharmProjects\mesh\autoencoder-for-denoising-coarser-mesh-based-numerical-solution")
#importing dependency
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import keras as K
import tensorflow.python.keras.backend as K
import tensorflow as tf
from sklearn.preprocessing import MinMaxScaler
from pyDOE import lhs
#tf.enable_eager_execution()
#tf.compat.v1.disable_eager_execution()
tf.compat.v1.disable_v2_behavior()

layers_c=[2, 50, 50, 50, 50, 50, 1]

layers_s=[2, 50, 50, 50, 50,50, 1]

x=np.linspace(0, 1, num=101)

x=x[:,None]

t=np.linspace(0, 6000, num=51)

t=t[:,None]

ic = np.concatenate((x, 0*x), 1)
x_ic=ic[:,0:1]
t_ic=ic[:,1:2]

boundary=(0,1)
cond_lb = np.concatenate((0*t + boundary[0], t), 1)
x_lb=cond_lb[:,0:1]
t_lb=cond_lb[:,1:2]
cond_rb = np.concatenate((0*t + boundary[1], t), 1)
x_rb=cond_rb[:,0:1]
t_rb=cond_rb[:,1:2]

c_dcl=1/(1 + np.exp(-0.02*(t-500)))

c_dcr=1/(1 + np.exp(-0.02*(-t+4100)))

c_dc=c_dcl*c_dcr

def sampling(minval,maxval,var,N):
    X = minval + (maxval-minval)*lhs(var, N)
    return X

data_f=sampling(np.array([0,0]),np.array([1,6000]),2,10000)
x_lhs=data_f[:,0:1]
t_lhs=data_f[:,1:2]

x=np.linspace(0, 1, num=21)

x=x[:,None]

t_f=np.linspace(0, 6000, num=21)

t_f=t_f[:,None]

xx,tt=np.meshgrid(x,t_f)
xx_f = xx.flatten()[:,None] # NT x 1
tt_f = tt.flatten()[:,None] # NT x 1

fp=np.concatenate((xx_f,tt_f),1)

def initialize_NN(layers):        
    weights = []
    biases = []
    num_layers = len(layers) 
    for l in range(0,num_layers-1):
        W = xavier_init(size=[layers[l], layers[l+1]])
        b = tf.Variable(tf.zeros([1,layers[l+1]], dtype=tf.float32), dtype=tf.float32)
        weights.append(W)
        biases.append(b)        
    return weights, biases

def xavier_init(size):
    in_dim = size[0]
    out_dim = size[1]        
    xavier_stddev = np.sqrt(2/(in_dim + out_dim))
    return tf.Variable(tf.compat.v1.random.truncated_normal([in_dim, out_dim], stddev=xavier_stddev), dtype=tf.float32)

#chamka..sigmoid function canged everything

def neural_net( X, weights, biases):
    num_layers = len(weights) + 1
    H = (X-minval)/(maxval-minval)
    for l in range(0,num_layers-2):
        W = weights[l]
        b = biases[l]
        #H = tf.tanh(tf.add(tf.matmul(H, W), b))
        H = tf.sigmoid(tf.add(tf.matmul(H, W), b))
    W = weights[-1]
    b = biases[-1]
    Y = tf.add(tf.matmul(H, W), b)
    return Y


"""
def net_NS_IC( x, y, t):
    c_ic = neural_net(tf.concat([x,y,t], 1), weights, biases)
    return c_ic
  """  
def net_NS( x, t,c_out,por,alpha):
    cx = tf.gradients(c_out, x)[0]
    ct = tf.gradients(c_out, t)[0]

    cxx = tf.gradients(cx, x)[0]
    ux=0.0003
    uy=0
    adv=ux*cx
    Dd=alpha*ux

    De=1e-9
   # ka=0.0008
   # kd=0.0001

    Jd=-(Dd+De)*(cxx)
    print("count",1)
    #breakpoint()
    fc=por*ct+adv+Jd
    return fc, Jd
#rho_b*s is state variable as s

def callback(loss):
    print('Loss: %.3e' % (loss))
#X = np.concatenate([x_train, y_train, t_train], 1)


#DEFINE THIS ONLY FOR INPUT DATA, IE FEATURES AND TAGER WHICH Has to be minimised
x_i=tf.compat.v1.placeholder(tf.float32, shape=[None, x_ic.shape[1]])

t_i=tf.compat.v1.placeholder(tf.float32, shape=[None, x_ic.shape[1]])

x_dcb=tf.compat.v1.placeholder(tf.float32, shape=[None, x_ic.shape[1]])

t_dcb=tf.compat.v1.placeholder(tf.float32, shape=[None, x_ic.shape[1]])

x_neb=tf.compat.v1.placeholder(tf.float32, shape=[None, x_ic.shape[1]])

t_neb=tf.compat.v1.placeholder(tf.float32, shape=[None, x_ic.shape[1]])

x_f=tf.compat.v1.placeholder(tf.float32, shape=[None, x_ic.shape[1]])
t_f=tf.compat.v1.placeholder(tf.float32, shape=[None, x_ic.shape[1]])

weights_c, biases_c = initialize_NN(layers_c)  

w_ic=tf.Variable(5.0)

w_dc=tf.Variable(3.0)
w_fc=tf.Variable(10000.4)

w_j=tf.Variable(1.0)

alpha=0.01
por=0.3

sess=tf.compat.v1.Session()
init = tf.compat.v1.global_variables_initializer()
sess.run(init)

minval=np.array([0,0])
maxval=np.array([1,6000])

tf_dict = {x_dcb: x_lb, t_dcb: t_lb, x_neb: x_rb, t_neb: t_rb, x_i: x_ic, t_i: t_ic, x_f: xx_f, t_f: tt_f}


tf_dict0 = {x_dcb: x_lb, t_dcb: t_lb, x_neb: x_rb, t_neb: t_rb, x_i: x_ic, t_i: t_ic, x_f: xx_f, t_f: tt_f}
#dict0 is define so that the samping happens on the original mesh, not the updated mesh with refine points
#tf_dict = { x_i: x_ic, y_i: y_ic, x_f: x_fp, y_f:y_fp, t_f:t_fp}


#c_dcb=neural_net(tf.concat([x_dcb, y_dcb], 1), weights_ib, biases_ib,np.array([0,1.5]),np.array([0,2.5]))
#c_dcb=neural_net(tf.concat([x_dcb, y_dcb], 1), weights_dcb, biases_dcb,np.array([0,1.5]),np.array([0,2.5]))
c_dcb=neural_net(tf.concat([x_dcb, t_dcb], 1), weights_c, biases_c)
c_neb=neural_net(tf.concat([x_neb, t_neb], 1), weights_c, biases_c)

c_ic=neural_net(tf.concat([x_i, t_i], 1), weights_c, biases_c)
c_f=neural_net(tf.concat([x_f, t_f], 1), weights_c,biases_c)

f,_=net_NS(x_f,t_f,c_f,por,alpha)

_,j=net_NS(x_neb,t_neb,c_neb,por,alpha)
"""
#adding 36 really worked out
loss_ic=36*tf.reduce_sum(abs(c_ic))
loss_dc=tf.reduce_sum(abs(c_dcb-c_dc))
#adding 36 really worked out
loss_f=tf.reduce_sum(abs(f))
loss_j=tf.reduce_sum(abs(j))
loss_all=loss_ic+loss_dc+loss_f+loss_j
ind_dc=loss_all/loss_dc
ind_ic=loss_all/loss_ic
ind_f=loss_all/loss_f
ind_j=loss_all/loss_j
"""
"""
conka=ka.eval(session=sess)
if conka<0 and conka>1:
    print("great")
    conka1=100
else:
    conka1=0

conkd=kd.eval(session=sess)
if conkd<0 and conkd>1:
    print("great")
    conkd1=100

else:
    conkd1=0
    
    """
#loss = 36*tf.reduce_sum(abs(c_ic))+tf.reduce_sum(abs(c_dcb-c_dc))+tf.reduce_sum(abs(f))+tf.reduce_sum(abs(j))
#tf.reduce_sum(abs(f)).eval(feed_dict=tf_dict,session=sess)
#add square 
#loss = w_ic*tf.reduce_sum(tf.square(c_ic))+w_is*tf.reduce_sum(tf.square(s_ic))+w_dc*tf.reduce_sum(tf.square(c_dcb-c_dc))+w_fc*tf.reduce_sum(tf.square(fc))+w_fs*tf.reduce_sum(tf.square(fs))+w_j*tf.reduce_sum(tf.square(j))
loss= w_ic*tf.reduce_sum(tf.square(c_ic))/len(x_ic)+w_dc*tf.reduce_sum(tf.square(c_dcb-c_dc))/len(x_lb)+w_fc*tf.reduce_sum(tf.square(f))/(len(xx_f))+w_j*tf.reduce_sum(tf.square(j))/len(x_rb)

#loss = tf.reduce_sum(tf.square(c_ic))+10*tf.reduce_sum(tf.square(s_ic))+tf.reduce_sum(tf.square(c_dcb-c_dc))+100*tf.reduce_sum(tf.square(fc))+10000*tf.reduce_sum(tf.square(fs))+tf.reduce_sum(tf.square(j))

optimizer_Adam = tf.compat.v1.train.AdamOptimizer(
    learning_rate=0.005, beta1=0.9, beta2=0.999, epsilon=1e-08, use_locking=False,
    name='Adam')

train_op_Adam = optimizer_Adam.minimize(loss,var_list=[weights_c,biases_c])  

import random
import math


#this just tells the existing points where error is more, also it gives resampling point from t raditional method
def errorpoints(r_value):
    r_sum= np.sum(r_value**k)

    prob_value=(r_value**k/r_sum)+c

    new=np.zeros(target)
    for i in range(target):
        new[i]=int(random.choices(range(len(prob_value)),prob_value)[0])  #index of fp selected according to thethe probability value, total index selected is same as how much we want
    #here random choice take index from 0 to all the collocation point, then prob_value assign the weight for it and a single element list is returned. 0 just take that single eklement out which is an integer

    prob_selected=[prob_value[int(i)] for i in new]      #probability of the points which got resampled, which is not imp for model, only for debug

    newpt=np.array([fp[int(i)] for i in new])     #all the swelected index according 
        
    return(newpt)

refine=1

#THIS IS SECONDARY FUNCTION. used inside a function. it gives refined points for a particluar point
def adap(x,t):
    gen=[]
    #normalising it so that point ccan be taken as radius of influence
    fpp=np.array([x/0.05,t/300])
    #print(fpp)
    count=0
    while True:    # number of refinement
        if count>refine-1:
            break
        px=random.uniform(-1, 1)
        pt=random.uniform(-1, 1)
        xnew=fpp[0]+px  #this works when we have 1 unit of distance seperation, if it is not one, we should take into accorunt distance, ie there
        tnew=fpp[1]+pt
        fppnew=np.array([xnew,tnew])
        #random points generated with range of 1,1 to -1-1 for the point 0 0
        #now we need to eliminate teh points who are far away
        dist=math.dist(fpp, fppnew)
        if dist<1:  #again this should be the minimum distance
            a=np.array([fppnew[0]*0.05,fppnew[1]*300])  #unormalise it
            if a[0]>0 and a[0]<1 and a[1]>0 and a[1]<6000 and a[1]>0:  #ensuring that it doesnt go beyond the dimension
                gen.append(a)
                count=count+1
    return np.array(gen)

#write code for definite number of refinement
#this code takes all the cordinates, and refine for all the points using above function. Then send it back
def resam(fp):
    gen_fin=[]
    for i in range(len(fp)):
        #print(i)
        gen=np.array(adap(fp[i,0],fp[i,1]))  #receiving n individual points in the dimension (n,2), where n is the number of point seeked for an individual original nesh point
        gen_fin.append(gen)  #repeating the activity for each original mesh point. Th mesh point now represnet, all refined ppoint ie for m points, m*n points of xt
    #to unbox gen from list to numpy
    ada=np.zeros([1,2])
    for n,i in enumerate(gen_fin):
        #print(n)
        if len(i)>0:
            ada=np.concatenate((ada,i),0)
    return ada

def amesh(admesh):
    newad=np.zeros((admesh,2))
    for i in range(admesh):
        newad[i,0]=random.uniform(0,1)    
        newad[i,1]=random.uniform(0,6000)
    return newad

sess=tf.compat.v1.Session()
init = tf.compat.v1.global_variables_initializer()
sess.run(init)   
target=100  #points to be selected for error refinement
adn=100
k=2
c=0
losstot=[]
nIter=1000

import time

# get the start time
st = time.time()


btcpd = pd.read_csv("btc2023.csv")

btc=btcpd.iloc[:,:].values

aa=np.array([x for x in range(51)])
aa=aa[:,None]

btc_imp=np.array([j for i,j in enumerate(btc) if  i% 60==0])

for it in range(1,nIter):
    sess.run(train_op_Adam, tf_dict)
    print(it)
    #fv=f.eval(feed_dict=tf_dict,session=sess)
    #print(it,loss_value,tf.reduce_sum(tf.square(c_dcb-c_dc)).eval(feed_dict=tf_dict,session=sess),tf.reduce_sum(tf.square(f)).eval(feed_dict=tf_dict,session=sess))
    loss_value=loss.eval(feed_dict=tf_dict0,session=sess)
    losstot.append(loss_value)
    if it%2000==0:

        r_val=f.eval(feed_dict=tf_dict0,session=sess)
       #actual points which got resampled
        resamp=errorpoints(r_val)
        
        refinep=resam(resamp)   #here gen_fin is list of refined point for each oriningal point, and aa is the list of all those refined points
        """
        #resampled=resam(newp)
        #print(resampled)
        #print("%%%%%%%", len(resampled))  
        xx_new=np.concatenate((xx_f,resamp[:,0:1]),0)
        tt_new=np.concatenate((tt_f,resamp[:,1:2]),0)  #it doesnt take the previous refined points
        loss= w_ic*tf.reduce_sum(tf.square(c_ic))/len(x_ic)+w_dc*tf.reduce_sum(tf.square(c_dcb-c_dc))/len(x_lb)+w_fc*tf.reduce_sum(tf.square(f))/(len(xx_new))+w_j*tf.reduce_sum(tf.square(j))/len(x_rb)
        tf_dict = {x_dcb: x_lb, t_dcb: t_lb, x_neb: x_rb, t_neb: t_rb, x_i: x_ic, t_i: t_ic, x_f: xx_new, t_f: tt_new}
        """
        #here we are making 400 random collocation points
        adappts=amesh(400)
        tf_dicta = {x_dcb: x_lb, t_dcb: t_lb, x_neb: x_rb, t_neb: t_rb, x_i: x_ic, t_i: t_ic, x_f: adappts[:,0:1], t_f: adappts[:,1:2]}
        #here we are finding out what is the error for all the random collocation points
        r_vala=f.eval(feed_dict=tf_dicta,session=sess)
        
        #here we are sorting the index of randpm points array according to their error
        sortadind=np.argsort(abs(r_vala[:,0]))
        #here we are selecting some points whose index corresponds to higher error
        sortad=np.zeros((adn,2))
        sortad=adappts[sortadind[-adn:],:]
        
        xx_new=np.concatenate((xx_f,sortad[:,0:1]),0)
        tt_new=np.concatenate((tt_f,sortad[:,1:2]),0) 
        
        loss= w_ic*tf.reduce_sum(tf.square(c_ic))/len(x_ic)+w_dc*tf.reduce_sum(tf.square(c_dcb-c_dc))/len(x_lb)+w_fc*tf.reduce_sum(tf.square(f))/(len(xx_new))+w_j*tf.reduce_sum(tf.square(j))/len(x_rb)
        tf_dict = {x_dcb: x_lb, t_dcb: t_lb, x_neb: x_rb, t_neb: t_rb, x_i: x_ic, t_i: t_ic, x_f: xx_new, t_f: tt_new}
        
        print(r_vala[sortadind[-10:],0])
        #c=neural_net(tf.concat([x1, t1], 1), weights, biases)
        cneb=c_neb.eval(feed_dict=tf_dict,session=sess)
        cdcb=c_dcb.eval(feed_dict=tf_dict,session=sess)
        plt.plot(aa[:,:]*2, cneb[:,:], marker='.', label="actual")
        plt.plot(aa[:,:]*2, cdcb[:,:], 'r', label="actual")
        plt.plot(aa[:,:]*2, c_dc[:,:], 'g', label="actual")
        plt.plot(aa[:,:]*2, btc_imp[:,:], 'g', label="actual")
        plt.show()
    print(it,loss_value)
    if abs(loss_value)<5e-6:
        break

et = time.time()

# get the execution time
elapsed_time = et - st



"""
to CONFIRM THE DISTANCE IS ONE out thedistance
fp=np.concatenate((xx_f/0.02,tt_f/20),1)
a=np.zeros(500)
b=np.zeros(500)
for j in range(1):
    print(j)
    dist=[math.dist(fp[j], fp[i]) for i in range(len(fp)) if i!=j]
    #a[j]=np.min([math.dist(fp[j], fp[i]) for i in range(len(fp)) if i!=j])
    b[j]=np.argmin(dist)
    a[j]=dist[int(b[j])]

plt.scatter(xx_f[:500]/0.01,tt_f[:500]/20)
"""

btcpd = pd.read_csv("btc2023.csv")

btc=btcpd.iloc[:,:].values

aa=np.array([x for x in range(51)])
aa=aa[:,None]

btc_imp=np.array([j for i,j in enumerate(btc) if  i% 60==0])

#c=neural_net(tf.concat([x1, t1], 1), weights, biases)
cneb=c_neb.eval(feed_dict=tf_dict,session=sess)
cdcb=c_dcb.eval(feed_dict=tf_dict,session=sess)
plt.plot(aa[:,:], cneb[:,:], marker='.', label="actual")
plt.plot(aa[:,:], cdcb[:,:], 'r', label="actual")
plt.plot(aa[:,:], c_dc[:,:], 'g', label="actual")
plt.plot(aa[:,:], btc_imp[:,:], 'g', label="actual")

from sklearn.metrics import r2_score

r2 = r2_score(btc_imp[:,:], cneb[:,:])

plt.scatter(xx_f,tt_f, marker='.',s=150)
#plt.scatter(xx_new,tt_new, marker='.')
plt.scatter(resamp[:,0],resamp[:,1],facecolors='none', edgecolors='r',s=150)
plt.scatter(refinep[:,0],refinep[:,1], marker='.', facecolors='green',s=150)
#plt.scatter(adappts[:,0],adappts[:,1], marker='.', facecolors='black')
plt.scatter(sortad[:,0],sortad[:,1], marker='.', facecolors='black',s=150)
plt.xticks(fontsize=14)
plt.yticks(fontsize=14)

#for plotting the zoom image
plt.scatter(xx_f,tt_f-1000, marker='.',s=1000)
#plt.scatter(xx_new,tt_new, marker='.')
plt.scatter(resamp[:,0],resamp[:,1]-1000,facecolors='none', edgecolors='r', s=1000)
plt.scatter(refinep[:,0],refinep[:,1]-1000, marker='.', facecolors='green', s=1000)
#plt.scatter(adappts[:,0],adappts[:,1], marker='.', facecolors='black')
plt.scatter(sortad[:,0],sortad[:,1]-1000, marker='.', facecolors='black', s=1000)
#plt.ylim(0, 5000)
plt.ylim(2500, 3400)
plt.xlim(0.28, 0.46)
plt.show()


from scipy.interpolate import interp2d

tf_dictorg = {x_dcb: x_lb, t_dcb: t_lb, x_neb: x_rb, t_neb: t_rb, x_i: x_ic, t_i: t_ic, x_f: xx_f, t_f: tt_f}

orig=c_f.eval(feed_dict=tf_dictorg,session=sess)

error=f.eval(feed_dict=tf_dictorg,session=sess)

result=np.concatenate((xx_f[:,0:1],tt_f[:,0:1],error[:,0:1]),axis=1)

import pandas as pd
df = pd.DataFrame(result)

df.to_csv("data2.csv", index=False)

"""


f = interp2d(xx_f,tt_f,orig,kind="linear")

x = np.arange(0,1,0.02)
y = np.arange(0,6000,120.0)
X,Y = np.meshgrid(x, y)

Z=f(x,y)

fig = plt.imshow(Z,extent=[np.min(x),np.max(x),np.min(y),np.max(y)])

plt.gca().set_xticks(range(len(x)))
plt.gca().set_yticks(range(len(y)))
plt.gca().set_xticklabels(x)
plt.gca().set_yticklabels(y)


plt.scatter(x_lhs,t_lhs, marker='.')


fp_lhs=np.concatenate((x_lhs/0.02,t_lhs/20),1)
a=np.zeros(len(fp_lhs))
b=np.zeros(len(fp_lhs))
for j in range(len(fp_lhs)):
    print(j)
    dist=[math.dist(fp_lhs[j], fp_lhs[i]) for i in range(len(fp_lhs)) if i!=j]
    #a[j]=np.min([math.dist(fp[j], fp[i]) for i in range(len(fp)) if i!=j])
    print(j)
    b[j]=np.argmin(dist)
    a[j]=dist[int(b[j])]

#hypothesis..we may not need myriads of sampling method wth this method
#show this by comparing lhs and unifrom without your method and with your method

colors = cm.rainbow(np.linspace(0, 1, len(a)))
for y, c in zip(a, colors):
    plt.scatter(x, y, color=c)

df = pd.DataFrame(a, columns=["x"])
sns.scatterplot(data=df, x="x", y="y")
import seaborn as sns
sns.scatterplot(data=df, x="x", y="y")
sns.color_palette("Spectral", as_cmap=True)

cmap=mpl.cm.viridis
# Plot...
fig, ax=plt.scatter(x_lhs, t_lhs,c=a, cmap=cmap, s=4)
import matplotlib as mpl
fig.colorbar(mpl.cm.ScalarMappable(cmap=cmap),
             cax=ax, orientation='horizontal', label='Some Units')
plt.show()

loss_trad = pd.read_csv("loss_trad.csv")

losstrad=loss_trad.iloc[:,:].values

bb=np.array([x for x in range(6000)])
plt.plot(bb, losstot, 'g', label="actual")

plt.plot(bb, losstrad[:,1], 'r', label="actual")

plt.plot(bb, losstot-losstrad[:,1], 'r', label="actual")



plt.plot(range(len(losstot)),losstot)

plt.ylim(0,0.00001)

plt.show()

"""