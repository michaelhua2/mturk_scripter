# mturk_scripter


There are five steps in running a user study on Amazon Mechanical Turk (AMT) with this repo. 
- Step 1: Create a folder of images
- Step 2: Host the folder on images on a publicly accessible server
- Step 3: Generate individual HIT files
- Step 4: Do a test run on aws sandbox to see if everything looks right
- Step 5: Run the HITs on aws live [THIS COSTS MONEY $$$]


## Step 1: Create a folder of images
This is dependant on your specific project. 
But the format needs to be something like:
```
BASE_FOLDER/
├── SUBFOLDER1/
│   ├── image1.jpg
│   ├── image2.jpg
│   └── ...
└── SUBFOLDER2/
    ├── image1.jpg
    ├── image2.jpg
    └── ...
```


## Step 2: Host the folder on images on a publicly accessible server



## Step 3: Generate individual HTML files
```
python src/my_html_maker_friendliness.py  -n ours_vs_sd_cvd_friendliness \
    --output_folder "outputs/mturk/cvd_friendliness/ours_vs_sd_friendliness_htmls_sandbox"

python src/my_html_maker_adherence.py  -n ours_vs_sd_prompt_adherence \
    --output_folder "outputs/mturk/prompt_adherence/ours_vs_sd_adherence_htmls_sandbox" 
# define the experiment configs in L14-29
```

## Step 4: Do a test run on aws sandbox to see if everything looks right
- Launch the command
```
# enter your access key and secret key in the L31-32
python src/my_hit_launcher.py \
    --folder "outputs/mturk/cvd_friendliness/ours_vs_sd_friendliness_htmls_sandbox" \
    --env_type "sandbox"
```

- Go to the sandbox link and complete the study manually
```
python src/result_parser.py \
    --folder "outputs/mturk/cvd_friendliness/ours_vs_sd_friendliness_htmls_sandbox" --env_type "sandbox"
```