
# parsetab.py
# This file is automatically generated. Do not edit.
# pylint: disable=W,C,R
_tabversion = '3.10'

_lr_method = 'LALR'

_lr_signature = 'leftANDORleftPLUSMINUSleftTIMESDIVIDEleftEQNELTGTLEGErightUPLUSUMINUSAND ASSIGN BEGIN COLON COMMA COMMENT DIVIDE DOUBLE_STRING END EQ FLOAT FUNCTION_NAME GE GT ID IF INTEGER LBRACE LBRACKET LE LPAREN LT MINUS NE NEWLINE OR PERIOD PLUS RBRACE RBRACKET RPAREN SEMI SINGLE_STRING THEN TIMES VARIABLEprogram : program statement\n               | statementstatement : ID ASSIGN expr SEMI\n                 | VARIABLE ID ASSIGN expr SEMIstatement : expr SEMIstatement : IF expr THEN BEGIN program ENDstatement : expr COMMA expr SEMIexpr : MINUS expr %prec UMINUS\n            | PLUS expr %prec UPLUSexpr : expr PLUS expr\n            | expr MINUS expr\n            | expr TIMES expr\n            | expr DIVIDE exprexpr : expr LT expr\n            | expr LE expr\n            | expr GT expr\n            | expr GE expr\n            | expr EQ expr\n            | expr NE expr\n            | expr AND expr\n            | expr OR exprexpr : LPAREN expr RPARENexpr : IDexpr : numberexpr : strexpr : FUNCTION_NAME LPAREN args RPAREN\n            | FUNCTION_NAME LPAREN RPAREN\n            | FUNCTION_NAME\n    args : args COMMA expr\n            | expr\n    number : INTEGER\n              | FLOAT\n              | INTEGER FLOAT\n    str : SINGLE_STRING\n           | DOUBLE_STRING'
    
_lr_action_items = {'ID':([0,1,2,5,6,7,8,9,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,39,55,61,62,64,66,67,68,70,],[3,3,-2,33,35,35,35,35,-1,35,-5,35,35,35,35,35,35,35,35,35,35,35,35,35,35,35,-3,-7,3,35,-4,3,-6,]),'VARIABLE':([0,1,2,17,19,61,62,64,67,68,70,],[5,5,-2,-1,-5,-3,-7,5,-4,5,-6,]),'IF':([0,1,2,17,19,61,62,64,67,68,70,],[6,6,-2,-1,-5,-3,-7,6,-4,6,-6,]),'MINUS':([0,1,2,3,4,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,57,59,60,61,62,63,64,65,66,67,68,69,70,],[7,7,-2,-23,22,7,7,7,7,-24,-25,-28,-31,-32,-34,-35,-1,7,-5,7,7,7,7,7,7,7,7,7,7,7,7,7,22,-23,-8,-9,22,7,-33,22,22,-10,-11,-12,-13,-14,-15,-16,-17,-18,-19,22,22,7,-22,-27,22,-3,-7,22,7,-26,7,-4,7,22,-6,]),'PLUS':([0,1,2,3,4,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,57,59,60,61,62,63,64,65,66,67,68,69,70,],[8,8,-2,-23,21,8,8,8,8,-24,-25,-28,-31,-32,-34,-35,-1,8,-5,8,8,8,8,8,8,8,8,8,8,8,8,8,21,-23,-8,-9,21,8,-33,21,21,-10,-11,-12,-13,-14,-15,-16,-17,-18,-19,21,21,8,-22,-27,21,-3,-7,21,8,-26,8,-4,8,21,-6,]),'LPAREN':([0,1,2,6,7,8,9,12,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,39,55,61,62,64,66,67,68,70,],[9,9,-2,9,9,9,9,39,-1,9,-5,9,9,9,9,9,9,9,9,9,9,9,9,9,9,9,-3,-7,9,9,-4,9,-6,]),'FUNCTION_NAME':([0,1,2,6,7,8,9,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,39,55,61,62,64,66,67,68,70,],[12,12,-2,12,12,12,12,-1,12,-5,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,-3,-7,12,12,-4,12,-6,]),'INTEGER':([0,1,2,6,7,8,9,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,39,55,61,62,64,66,67,68,70,],[13,13,-2,13,13,13,13,-1,13,-5,13,13,13,13,13,13,13,13,13,13,13,13,13,13,13,-3,-7,13,13,-4,13,-6,]),'FLOAT':([0,1,2,6,7,8,9,13,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,39,55,61,62,64,66,67,68,70,],[14,14,-2,14,14,14,14,40,-1,14,-5,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,-3,-7,14,14,-4,14,-6,]),'SINGLE_STRING':([0,1,2,6,7,8,9,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,39,55,61,62,64,66,67,68,70,],[15,15,-2,15,15,15,15,-1,15,-5,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,-3,-7,15,15,-4,15,-6,]),'DOUBLE_STRING':([0,1,2,6,7,8,9,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,39,55,61,62,64,66,67,68,70,],[16,16,-2,16,16,16,16,-1,16,-5,16,16,16,16,16,16,16,16,16,16,16,16,16,16,16,-3,-7,16,16,-4,16,-6,]),'$end':([1,2,17,19,61,62,67,70,],[0,-2,-1,-5,-3,-7,-4,-6,]),'END':([2,17,19,61,62,67,68,70,],[-2,-1,-5,-3,-7,-4,70,-6,]),'ASSIGN':([3,33,],[18,55,]),'SEMI':([3,4,10,11,12,13,14,15,16,35,36,37,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,57,59,63,65,],[-23,19,-24,-25,-28,-31,-32,-34,-35,-23,-8,-9,-33,61,62,-10,-11,-12,-13,-14,-15,-16,-17,-18,-19,-20,-21,-22,-27,67,-26,]),'COMMA':([3,4,10,11,12,13,14,15,16,35,36,37,40,43,44,45,46,47,48,49,50,51,52,53,54,57,58,59,60,65,69,],[-23,20,-24,-25,-28,-31,-32,-34,-35,-23,-8,-9,-33,-10,-11,-12,-13,-14,-15,-16,-17,-18,-19,-20,-21,-22,66,-27,-30,-26,-29,]),'TIMES':([3,4,10,11,12,13,14,15,16,34,35,36,37,38,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,57,59,60,63,65,69,],[-23,23,-24,-25,-28,-31,-32,-34,-35,23,-23,-8,-9,23,-33,23,23,23,23,-12,-13,-14,-15,-16,-17,-18,-19,23,23,-22,-27,23,23,-26,23,]),'DIVIDE':([3,4,10,11,12,13,14,15,16,34,35,36,37,38,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,57,59,60,63,65,69,],[-23,24,-24,-25,-28,-31,-32,-34,-35,24,-23,-8,-9,24,-33,24,24,24,24,-12,-13,-14,-15,-16,-17,-18,-19,24,24,-22,-27,24,24,-26,24,]),'LT':([3,4,10,11,12,13,14,15,16,34,35,36,37,38,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,57,59,60,63,65,69,],[-23,25,-24,-25,-28,-31,-32,-34,-35,25,-23,-8,-9,25,-33,25,25,25,25,25,25,-14,-15,-16,-17,-18,-19,25,25,-22,-27,25,25,-26,25,]),'LE':([3,4,10,11,12,13,14,15,16,34,35,36,37,38,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,57,59,60,63,65,69,],[-23,26,-24,-25,-28,-31,-32,-34,-35,26,-23,-8,-9,26,-33,26,26,26,26,26,26,-14,-15,-16,-17,-18,-19,26,26,-22,-27,26,26,-26,26,]),'GT':([3,4,10,11,12,13,14,15,16,34,35,36,37,38,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,57,59,60,63,65,69,],[-23,27,-24,-25,-28,-31,-32,-34,-35,27,-23,-8,-9,27,-33,27,27,27,27,27,27,-14,-15,-16,-17,-18,-19,27,27,-22,-27,27,27,-26,27,]),'GE':([3,4,10,11,12,13,14,15,16,34,35,36,37,38,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,57,59,60,63,65,69,],[-23,28,-24,-25,-28,-31,-32,-34,-35,28,-23,-8,-9,28,-33,28,28,28,28,28,28,-14,-15,-16,-17,-18,-19,28,28,-22,-27,28,28,-26,28,]),'EQ':([3,4,10,11,12,13,14,15,16,34,35,36,37,38,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,57,59,60,63,65,69,],[-23,29,-24,-25,-28,-31,-32,-34,-35,29,-23,-8,-9,29,-33,29,29,29,29,29,29,-14,-15,-16,-17,-18,-19,29,29,-22,-27,29,29,-26,29,]),'NE':([3,4,10,11,12,13,14,15,16,34,35,36,37,38,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,57,59,60,63,65,69,],[-23,30,-24,-25,-28,-31,-32,-34,-35,30,-23,-8,-9,30,-33,30,30,30,30,30,30,-14,-15,-16,-17,-18,-19,30,30,-22,-27,30,30,-26,30,]),'AND':([3,4,10,11,12,13,14,15,16,34,35,36,37,38,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,57,59,60,63,65,69,],[-23,31,-24,-25,-28,-31,-32,-34,-35,31,-23,-8,-9,31,-33,31,31,-10,-11,-12,-13,-14,-15,-16,-17,-18,-19,-20,-21,-22,-27,31,31,-26,31,]),'OR':([3,4,10,11,12,13,14,15,16,34,35,36,37,38,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,57,59,60,63,65,69,],[-23,32,-24,-25,-28,-31,-32,-34,-35,32,-23,-8,-9,32,-33,32,32,-10,-11,-12,-13,-14,-15,-16,-17,-18,-19,-20,-21,-22,-27,32,32,-26,32,]),'THEN':([10,11,12,13,14,15,16,34,35,36,37,40,43,44,45,46,47,48,49,50,51,52,53,54,57,59,65,],[-24,-25,-28,-31,-32,-34,-35,56,-23,-8,-9,-33,-10,-11,-12,-13,-14,-15,-16,-17,-18,-19,-20,-21,-22,-27,-26,]),'RPAREN':([10,11,12,13,14,15,16,35,36,37,38,39,40,43,44,45,46,47,48,49,50,51,52,53,54,57,58,59,60,65,69,],[-24,-25,-28,-31,-32,-34,-35,-23,-8,-9,57,59,-33,-10,-11,-12,-13,-14,-15,-16,-17,-18,-19,-20,-21,-22,65,-27,-30,-26,-29,]),'BEGIN':([56,],[64,]),}

_lr_action = {}
for _k, _v in _lr_action_items.items():
   for _x,_y in zip(_v[0],_v[1]):
      if not _x in _lr_action:  _lr_action[_x] = {}
      _lr_action[_x][_k] = _y
del _lr_action_items

_lr_goto_items = {'program':([0,64,],[1,68,]),'statement':([0,1,64,68,],[2,17,2,17,]),'expr':([0,1,6,7,8,9,18,20,21,22,23,24,25,26,27,28,29,30,31,32,39,55,64,66,68,],[4,4,34,36,37,38,41,42,43,44,45,46,47,48,49,50,51,52,53,54,60,63,4,69,4,]),'number':([0,1,6,7,8,9,18,20,21,22,23,24,25,26,27,28,29,30,31,32,39,55,64,66,68,],[10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,]),'str':([0,1,6,7,8,9,18,20,21,22,23,24,25,26,27,28,29,30,31,32,39,55,64,66,68,],[11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,]),'args':([39,],[58,]),}

_lr_goto = {}
for _k, _v in _lr_goto_items.items():
   for _x, _y in zip(_v[0], _v[1]):
       if not _x in _lr_goto: _lr_goto[_x] = {}
       _lr_goto[_x][_k] = _y
del _lr_goto_items
_lr_productions = [
  ("S' -> program","S'",1,None,None,None),
  ('program -> program statement','program',2,'p_program','myparser.py',20),
  ('program -> statement','program',1,'p_program','myparser.py',21),
  ('statement -> ID ASSIGN expr SEMI','statement',4,'p_statement_assign','myparser.py',31),
  ('statement -> VARIABLE ID ASSIGN expr SEMI','statement',5,'p_statement_assign','myparser.py',32),
  ('statement -> expr SEMI','statement',2,'p_statement_expr','myparser.py',50),
  ('statement -> IF expr THEN BEGIN program END','statement',6,'p_statement_ifthen','myparser.py',56),
  ('statement -> expr COMMA expr SEMI','statement',4,'p_statement_ifcomma','myparser.py',62),
  ('expr -> MINUS expr','expr',2,'p_expr_unary','myparser.py',68),
  ('expr -> PLUS expr','expr',2,'p_expr_unary','myparser.py',69),
  ('expr -> expr PLUS expr','expr',3,'p_expr_binop','myparser.py',77),
  ('expr -> expr MINUS expr','expr',3,'p_expr_binop','myparser.py',78),
  ('expr -> expr TIMES expr','expr',3,'p_expr_binop','myparser.py',79),
  ('expr -> expr DIVIDE expr','expr',3,'p_expr_binop','myparser.py',80),
  ('expr -> expr LT expr','expr',3,'p_expr_relation','myparser.py',88),
  ('expr -> expr LE expr','expr',3,'p_expr_relation','myparser.py',89),
  ('expr -> expr GT expr','expr',3,'p_expr_relation','myparser.py',90),
  ('expr -> expr GE expr','expr',3,'p_expr_relation','myparser.py',91),
  ('expr -> expr EQ expr','expr',3,'p_expr_relation','myparser.py',92),
  ('expr -> expr NE expr','expr',3,'p_expr_relation','myparser.py',93),
  ('expr -> expr AND expr','expr',3,'p_expr_relation','myparser.py',94),
  ('expr -> expr OR expr','expr',3,'p_expr_relation','myparser.py',95),
  ('expr -> LPAREN expr RPAREN','expr',3,'p_expr_group','myparser.py',103),
  ('expr -> ID','expr',1,'p_expr_id','myparser.py',111),
  ('expr -> number','expr',1,'p_expr_number','myparser.py',117),
  ('expr -> str','expr',1,'p_expr_str','myparser.py',124),
  ('expr -> FUNCTION_NAME LPAREN args RPAREN','expr',4,'p_expr_function','myparser.py',131),
  ('expr -> FUNCTION_NAME LPAREN RPAREN','expr',3,'p_expr_function','myparser.py',132),
  ('expr -> FUNCTION_NAME','expr',1,'p_expr_function','myparser.py',133),
  ('args -> args COMMA expr','args',3,'p_args','myparser.py',145),
  ('args -> expr','args',1,'p_args','myparser.py',146),
  ('number -> INTEGER','number',1,'p_number','myparser.py',155),
  ('number -> FLOAT','number',1,'p_number','myparser.py',156),
  ('number -> INTEGER FLOAT','number',2,'p_number','myparser.py',157),
  ('str -> SINGLE_STRING','str',1,'p_str','myparser.py',165),
  ('str -> DOUBLE_STRING','str',1,'p_str','myparser.py',166),
]
