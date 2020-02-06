import argparse
import os
import textattack
import time

RECIPE_NAMES = {
    'alzantot':      'textattack.attack_recipes.Alzantot2018GeneticAlgorithm',
    'alz-adjusted':  'textattack.attack_recipes.Alzantot2018GeneticAlgorithmAdjusted',
    'textfooler':    'textattack.attack_recipes.Jin2019TextFooler',
    'tf-adjusted':   'textattack.attack_recipes.Jin2019TextFoolerAdjusted',
}

MODEL_CLASS_NAMES = {
    #
    # Text classification models
    #
    
    # BERT models - default uncased
    'bert-ag-news':             'textattack.models.classification.bert.BERTForAGNewsClassification',
    'bert-imdb':                'textattack.models.classification.bert.BERTForIMDBSentimentClassification',
    'bert-mr':                  'textattack.models.classification.bert.BERTForMRSentimentClassification',
    'bert-yelp-sentiment':      'textattack.models.classification.bert.BERTForYelpSentimentClassification',
    # CNN models
    'cnn-ag-news':              'textattack.models.classification.cnn.WordCNNForAGNewsClassification',
    'cnn-imdb':                 'textattack.models.classification.cnn.WordCNNForIMDBSentimentClassification',
    'cnn-mr':                   'textattack.models.classification.cnn.WordCNNForMRSentimentClassification',
    'cnn-yelp-sentiment':       'textattack.models.classification.cnn.WordCNNForYelpSentimentClassification',
    # LSTM models
    'lstm-ag-news':             'textattack.models.classification.lstm.LSTMForAGNewsClassification',
    'lstm-imdb':                'textattack.models.classification.lstm.LSTMForIMDBSentimentClassification',
    'lstm-mr':                  'textattack.models.classification.lstm.LSTMForMRSentimentClassification',
    'lstm-yelp-sentiment':      'textattack.models.classification.lstm.LSTMForYelpSentimentClassification',
    
    #
    # Textual entailment models
    #
    
    # BERT models
    'bert-mnli':                'textattack.models.entailment.bert.BERTForMNLI',
    'bert-snli':                'textattack.models.entailment.bert.BERTForSNLI',
}

DATASET_BY_MODEL = {
    #
    # Text classification datasets
    #
    
    # AG News
    'bert-ag-news':             textattack.datasets.classification.AGNews,
    'cnn-ag-news':              textattack.datasets.classification.AGNews,
    'lstm-ag-news':             textattack.datasets.classification.AGNews,
    # IMDB 
    'bert-imdb':                textattack.datasets.classification.IMDBSentiment,
    'cnn-imdb':                 textattack.datasets.classification.IMDBSentiment,
    'lstm-imdb':                textattack.datasets.classification.IMDBSentiment,
    # MR
    'bert-mr':                  textattack.datasets.classification.MovieReviewSentiment,
    'cnn-mr':                   textattack.datasets.classification.MovieReviewSentiment,
    'lstm-mr':                  textattack.datasets.classification.MovieReviewSentiment,
    # Yelp
    'bert-yelp-sentiment':      textattack.datasets.classification.YelpSentiment,
    'cnn-yelp-sentiment':       textattack.datasets.classification.YelpSentiment,
    'lstm-yelp-sentiment':      textattack.datasets.classification.YelpSentiment,
    
    #
    # Textual entailment datasets
    #
    'bert-mnli':                textattack.datasets.entailment.MNLI,
    'bert-snli':                textattack.datasets.entailment.SNLI,
}

TRANSFORMATION_CLASS_NAMES = {
    'word-swap-embedding':             'textattack.transformations.WordSwapEmbedding',
    'word-swap-homoglyph':             'textattack.transformations.WordSwapHomoglyph',
    'word-swap-neighboring-char-swap': 'textattack.transformations.WordSwapNeighboringCharacterSwap',
}

CONSTRAINT_CLASS_NAMES = {
    'embedding':    'textattack.constraints.semantics.WordEmbeddingDistance',
    'goog-lm':      'textattack.constraints.semantics.language_models.GoogleLanguageModel',
    'bert':         'textattack.constraints.semantics.sentence_encoders.BERT',
    'infer-sent':   'textattack.constraints.semantics.sentence_encoders.InferSent',
    'use':          'textattack.constraints.semantics.sentence_encoders.UniversalSentenceEncoder',
    'lang-tool':    'textattack.constraints.syntax.LanguageTool', 
}

ATTACK_CLASS_NAMES = {
    'greedy-word':        'textattack.attack_methods.GreedyWordSwap',
    'ga-word':            'textattack.attack_methods.GeneticAlgorithm',
    'greedy-word-wir':    'textattack.attack_methods.GreedyWordSwapWIR',
}


def get_args():
    parser = argparse.ArgumentParser(
        description='A commandline parser for TextAttack', 
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('--transformation', type=str, required=False,
        default='word-swap-embedding', choices=TRANSFORMATION_CLASS_NAMES.keys(),
        help='The transformations to apply.')
        
    parser.add_argument('--model', type=str, required=False, default='bert-yelp-sentiment',
        choices=MODEL_CLASS_NAMES.keys(), help='The classification model to attack.')
    
    parser.add_argument('--constraints', type=str, required=False, nargs='*',
        default=[], choices=CONSTRAINT_CLASS_NAMES.keys(),
        help=('Constraints to add to the attack. Usage: "--constraints {constraint}:{arg_1}={value_1},{arg_3}={value_3}"'))
    
    parser.add_argument('--out_dir', type=str, required=False, default=None,
        help='A directory to output results to.')
    
    parser.add_argument('--enable_visdom', action='store_true',
        help='Enable logging to visdom.')
    
    parser.add_argument('--disable_stdout', action='store_true',
        help='Disable logging to stdout')
   
    parser.add_argument('--enable_csv', nargs='?', default=None, const='fancy', type=str,
        help='Enable logging to csv. Use --enable_csv plain to remove [[]] around words.')

    parser.add_argument('--num_examples', '-n', type=int, required=False, 
        default='5', help='The number of examples to process.')
    
    parser.add_argument('--num_examples_offset', '-o', type=int, required=False, 
        default=0, help='The offset to start at in the dataset.')

    parser.add_argument('--shuffle', action='store_true', required=False, 
        default=False, help='Randomly shuffle the data before attacking')
    
    parser.add_argument('--interactive', action='store_true', default=False,
        help='Whether to run attacks interactively.')
    
    attack_group = parser.add_mutually_exclusive_group(required=False)
    
    attack_group.add_argument('--attack', '--attack_method', type=str, 
        required=False, default='greedy-word-wir', 
        help='The type of attack to run.', choices=ATTACK_CLASS_NAMES.keys())
    
    attack_group.add_argument('--recipe', type=str, required=False, default=None,
        help='full attack recipe (overrides provided transformation & constraints)',
        choices=RECIPE_NAMES.keys())
    
    args = parser.parse_args()
    
    return args

def parse_transformation_from_args(args):
    # Transformations
    _transformation = []    
    transformation = args.transformation
    if ':' in transformation:
        transformation_name, params = transformation.split(':')
        if transformation_name not in TRANSFORMATION_CLASS_NAMES:
            raise ValueError(f'Error: unsupported transformation {transformation_name}')
        transformation = eval(f'{TRANSFORMATION_CLASS_NAMES[transformation_name]}({params})')
    elif transformation in TRANSFORMATION_CLASS_NAMES:
        transformation = eval(f'{TRANSFORMATION_CLASS_NAMES[transformation]}()')
    else:
        raise ValueError(f'Error: unsupported transformation {transformation}')
    return transformation

def parse_constraints_from_args(args):
    # Constraints
    if not args.constraints: 
        return []
    
    _constraints = []
    for constraint in args.constraints:
        if ':' in constraint:
            constraint_name, params = constraint.split(':')
            if constraint_name not in CONSTRAINT_CLASS_NAMES:
                raise ValueError(f'Error: unsupported constraint {constraint_name}')
            _constraints.append(eval(f'{CONSTRAINT_CLASS_NAMES[constraint_name]}({params})'))
        elif constraint in CONSTRAINT_CLASS_NAMES:
            _constraints.append(eval(f'{CONSTRAINT_CLASS_NAMES[constraint]}()'))
        else:
            raise ValueError(f'Error: unsupported constraint {constraint}')
    
    return _constraints

def parse_recipe_from_args(model, args):
    if ':' in args.recipe:
        recipe_name, params = args.recipe.split(':')
        if recipe_name not in RECIPE_NAMES:
            raise ValueError(f'Error: unsupported recipe {recipe_name}')
        recipe = eval(f'{RECIPE_NAMES[recipe_name]}(model, {params})')
    elif args.recipe in RECIPE_NAMES:
        recipe = eval(f'{RECIPE_NAMES[args.recipe]}(model)')
    else:
        raise ValueError('Invalid recipe {args.recipe}')
    return recipe

def parse_model_and_attack_from_args(args):
    if ':' in args.model:
        model_name, params = args.model.split(':')
        if model_name not in MODEL_CLASS_NAMES:
            raise ValueError(f'Error: unsupported model {model_name}')
        model = eval(f'{MODEL_CLASS_NAMES[model_name]}({params})')
    elif args.model in MODEL_CLASS_NAMES:
        model = eval(f'{MODEL_CLASS_NAMES[args.model]}()')
    else: 
        raise ValueError(f'Error: unsupported model {args.model}')
    if args.recipe:
        attack = parse_recipe_from_args(model, args)
    else:
        transformation = parse_transformation_from_args(args)
        constraints = parse_constraints_from_args(args)
        if ':' in args.attack:
            attack_name, params = args.attack.split(':')
            if attack_name not in ATTACK_CLASS_NAMES:
                raise ValueError(f'Error: unsupported attack {attack_name}')
            attack = eval(f'{ATTACK_CLASS_NAMES[attack_name]}(model, transformation, constraints=constraints, {params})')
        elif args.attack in ATTACK_CLASS_NAMES:
            attack = eval(f'{ATTACK_CLASS_NAMES[args.attack]}(model, transformation, constraints=constraints)')
        else:
            raise ValueError(f'Error: unsupported attack {args.attack}')
    return model, attack

def parse_logger_from_args(args):# Create logger
    attack_logger = textattack.loggers.AttackLogger()
    # Set default output directory to `textattack/outputs`.
    if not args.out_dir:
        current_dir = os.path.dirname(os.path.realpath(__file__))
        outputs_dir = os.path.join(current_dir, os.pardir, 'outputs')
        args.out_dir = outputs_dir
        
    # Output file.
    out_time = int(time.time()*1000) # Output file
    outfile_name = 'attack-{}.txt'.format(out_time)
    attack_logger.add_output_file(os.path.join(args.out_dir, outfile_name))
        
    # CSV
    if args.enable_csv:
        outfile_name = 'attack-{}.csv'.format(out_time)
        plain = args.enable_csv == 'plain'
        csv_path = os.path.join(args.out_dir, outfile_name)
        attack_logger.add_output_csv(csv_path, plain)
        print('Logging to CSV at path {}.'.format(csv_path))

    # Visdom
    if args.enable_visdom:
        attack_logger.enable_visdom()

    # Stdout
    if not args.disable_stdout:
        attack_logger.enable_stdout()
    return attack_logger