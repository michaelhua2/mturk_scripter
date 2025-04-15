import os, sys, ipdb, argparse, string, json
import numpy as np


def fileread(str,breakcode='[[BR]]'):
    fid = open(str,'r')
    a = fid.readlines()
    fid.close()
    return breakcode.join(a)


def getOpts(expt_name):
    opt = getDefaultOpts()
    opt['gt_path'] = 'sd_friendliness'
    opt['which_algs_paths'] = ['ours_friendliness']
    opt['Nimgs'] = 10
    opt['Npairs'] = 10
    opt['Npractice'] = 0
    opt['Nhits'] = 1
    opt['ut_id'] = 'NA'
    opt['base_url'] = 'http://baymax.ri.cmu.edu:8001/outputs/tests/mturk/'
    opt['instructions_file'] = 'templates/friendliness/instructions_basic_identity.html'
    opt['short_instructions_file'] = 'templates/friendliness/short_instructions_identity.html'
    opt['consent_file'] = 'templates/friendliness/consent_basic.html'
    opt['use_vigilance'] = False
    opt['paired'] = True
    opt['im_height'] = 400
    opt['im_width'] = 400
    opt['expt_name'] = expt_name
    return opt


def getDefaultOpts():
    opt = {}
    opt['expt_name'] = 'unset'
    opt['which_algs_paths'] = 'unset'		 # paths to images generated by algoritms, e.g. {'my_alg','baseline_alg'}
    opt['vigilance_path'] = 'vigilance'	   # path to vigilance images
    opt['gt_path'] = 'gt'					 # path to gt images
    opt['Nimgs'] = 100						# number of images to test
    opt['Npairs'] = 60						# number of paired comparisons per HIT
    opt['Npractice'] = 10					 # number of practice trials per HIT (number of non-practice trials is opt['Npairs']-opt['Npractice'])
    opt['Nhits'] = 50				 # number of HITs per algorithm
    opt['vigilance_freq'] = 0.0			   # percent of trials that are vigilance tests
    opt['use_vigilance'] = False			   # include vigilance trials (obviously fake images to check that Turkers are paying attention)	
    opt['ut_id'] = 'unset'					# set this using http://uniqueturker.myleott.com/
    opt['base_url'] = 'unset'				 # url where images to test are accessible as "opt['base_url']/n.png", for integers n
    opt['instructions_file'] = 'instructions_basic.html'		# instructions appear at the beginning of the HIT
    opt['short_instructions_file'] = 'short_instructions_basic.html'  # short instructions are shown at the top of every trial
    opt['consent_file'] = 'consent_basic.html'			 # informed consent text appears the beginning of the HIT
    
    opt['paired'] = True					  # if True, then fake/n.jpg will be pitted against real/n.jpg; if false, fake/n.jpg will be pitted against real/m.jpg, for random n and m
    opt['filename'] = lambda x : f'{x}.jpg'
    return opt


def checkOpts(opt):
    if(opt['which_algs_paths']=='unset'):
        print('must provide a list of algorithms to test')
    # if(opt['ut_id']=='unset'):
    #     print('must set a unique id for this HIT using http://uniqueturker.myleott.com/')
    if(opt['base_url']=='unset'):
        print('must provide a url where test images are accessible')
    if(opt['instructions_file']=='unset'):
        print('must provide a file containing html formatted instructions to display once at start of experiment')
    if(opt['short_instructions_file']=='unset'):
        print('must provide a file containing html formatted instructions to display on each trial')
    if(opt['consent_file']=='unset'):
        print('must provide a file containing html formatted infromed consent test, display at start of experiment')


def mk_expt(args):
    expt_name = args.name
    opt = getOpts(expt_name)
    checkOpts(opt)
    os.makedirs(os.path.join(args.output_folder, "htmls"), exist_ok=True)
    
    # make header
    head_gt_side, head_images_left, head_images_right = [], [], []
    
    for i in range(opt['Npairs']):
        head_gt_side.append('gt_side%d'%i)
        head_images_left.append('images_left%d'%i)
        head_images_right.append('images_right%d'%i)
    head_gt_side = [head_gt_side,]
    head_images_left = [head_images_left,]
    head_images_right = [head_images_right,]
    
    assert opt['paired']
    assert len(opt['which_algs_paths'])==1

    # i get a total of HxN number of comparisons
    A = len(opt['which_algs_paths']) # = 1 
    H = opt['Nhits'] # number of hits
    I = opt['Nimgs'] # = 500
    N = opt['Npairs'] # number of images per hit = 20

    # make sure H*N = I


    which_alg = np.random.randint(A, size=H*N)

    # img_indices = np.arange(I)
    img_indices = []
    for i in range(I):
        for seed in range(5):
            img_indices.append(f"{i}_{seed}_")
    img_indices = np.array(img_indices)
    # shuffle the indices with a fixed seed
    np.random.seed(0)
    np.random.shuffle(img_indices)

    which_ind0 = which_ind1 = img_indices
    which_side = np.random.randint(2, size=H*N) # randomize left or right
    vigilance = (np.random.rand(H*N) < opt['vigilance_freq']) * opt['use_vigilance']

    gt_side = []
    images_left = []
    images_right = []
    images_input = []
    all_captions = json.load(open("captions.json", 'r'))
    captions = []
    for (nn,data) in enumerate(zip(which_alg,which_ind0,which_ind1,which_side,vigilance)):
        cur_which_alg, cur_which_ind0, cur_which_ind1, cur_which_side, cur_vigilance = data
        assert cur_which_ind0==cur_which_ind1
        assert cur_which_alg == 0
        cur_alg_name = opt['which_algs_paths'][cur_which_alg] if not cur_vigilance else opt['vigilance_path']
        if(cur_which_side==0):
            gt_side.append('left')
            images_left.append(('%s/'+opt['filename'](cur_which_ind0))%opt['gt_path'])
            images_right.append(('%s/'+opt['filename'](cur_which_ind1))%cur_alg_name)
        else:
            gt_side.append('right')
            images_left.append(('%s/'+opt['filename'](cur_which_ind0))%cur_alg_name)
            images_right.append(('%s/'+opt['filename'](cur_which_ind1))%opt['gt_path'])
        images_input.append(('%s/'+opt['filename'](cur_which_ind0))%cur_alg_name)
        caption = all_captions[int(cur_which_ind0.split('_')[0])]
        captions.append(caption)
    
    gt_side = np.array(gt_side).reshape((H,N))
    images_left = np.array(images_left).reshape((H,N))
    images_right = np.array(images_right).reshape((H,N))
    images_input = np.array(images_input).reshape((H,N))
    captions = np.array(captions).reshape((H,N))
    head_gt_side = np.array(head_gt_side)
    head_images_left = np.array(head_images_left)
    head_images_right = np.array(head_images_right)
    
    captions = np.array(captions).reshape((H,N))
    
    breakcode='[[BR]]'

    # make an HTML file for each HIT
    for HIT_IDX in range(H):
        html = fileread('src/mturk_scripts/templates/index_template_friendliness.html', breakcode=breakcode)
        html = html.replace('{{UT_ID}}', opt['ut_id'])
        html = html.replace('{{BASE_URL}}', opt['base_url'])
        html = html.replace('{{INSTRUCTIONS}}', fileread(opt['instructions_file'], breakcode=breakcode))
        html = html.replace('{{SHORT_INSTRUCTIONS}}', fileread(opt['short_instructions_file'], breakcode=breakcode))
        html = html.replace('{{CAPTION}}', f"{HIT_IDX}")
        html = html.replace('{{CONSENT}}', fileread(opt['consent_file'], breakcode=breakcode))
        html = html.replace('{{IM_DIV_HEIGHT}}', '%i'%(50+2))
        html = html.replace('{{IM_DIV_WIDTH}}', '%i'%(opt['im_width']+2))
        html = html.replace('{{IM_HEIGHT}}', '%i'%(opt['im_height']))
        html = html.replace('{{IM_WIDTH}}', '%i'%(opt['im_width']))
        html = html.replace('{{N_PRACTICE}}', '%i'%(opt['Npractice']))
        html = html.replace('{{TOTAL_NUM_IMS}}', '%i'%(opt['Npairs']))
        # ipdb.set_trace()
        s = (' ').join([f'sequence_helper("{gt_side[HIT_IDX][i]}","{images_left[HIT_IDX][i]}","{images_right[HIT_IDX][i]}", "{captions[HIT_IDX][i]}");\n' for i in range(opt['Npairs'])]) 
        html = html.replace('{{SEQUENCE}}', s)
        s = (' ').join(['<input type="hidden" name="selection%d" id="selection%d" value="unset">\n'%(i,i) for i in range(opt['Npairs'])])
        html = html.replace('{{SELECTION}}', s)
        
        with open(os.path.join(args.output_folder,f'htmls/index_{HIT_IDX}.html'),'w') as f:
            f.writelines(html.split(breakcode))


parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('-n','--name', type=str, default='experiments name')
parser.add_argument('--output_folder', type=str)

args = parser.parse_args()
mk_expt(args)