*
* AUTHOR: Sascha Kuhnke
* Created: 16.07.2019
*

SETS
	
	WS				water sources
	CO				contaminants;

$if not set gdxincname $abort 'No include file name for data file provided'
$gdxin %gdxincname%
$load WS CO


PARAMETERS

* General
	IS_PRED(WS)				equals to 1 if WS is a predecessor of WD

* Water Sources
	PO_WS(WS, CO)			contaminant concentration leaving source	

* Water Demands
	PO_MIN_WD(CO)			minimum allowed contaminant concentration	
	PO_MAX_WD(CO)			maximum allowed contaminant concentration;	

$load PO_WS


SCALARS

	ZERO					equals zero								/ 0 /
	ONE						equals one								/ 1 /
	FEAS_TOLERANCE			feasibility tolerance
	
	MODEL_STATUS			model solution status		
	SOLVE_STATUS			solver termination condition
	OBJEST					estimate of the best possible solution
	OBJVAL					objective function value;

$load FEAS_TOLERANCE
$gdxin


POSITIVE VARIABLES

* Relative Flows
	XI(WS)				relative flow in pipe;


VARIABLE

	OBJ					objective function;


EQUATIONS

* Constraints
	REL_FL_MIN(CO)
	REL_FL_MAX(CO)
	REL_FL_SOS 

	OBJECTIVE;


* Constraints
	REL_FL_MIN(CO) ..			SUM(WS, PO_WS(WS, CO) * IS_PRED(WS) * XI(WS)) 		=G=		PO_MIN_WD(CO);
	REL_FL_MAX(CO) ..			SUM(WS, PO_WS(WS, CO) * IS_PRED(WS) * XI(WS)) 		=L=		PO_MAX_WD(CO);
	REL_FL_SOS ..				SUM(WS, IS_PRED(WS) * XI(WS)) 						=E= 	ONE;
	

* Objective Function
	OBJECTIVE .. 			OBJ 	=E=	 	ZERO;


MODEL

	PREPROCESSING / ALL /;	


OPTION

	threads = 1
	sysOut = ON;


PREPROCESSING.holdfixed = 1;
PREPROCESSING.tolInfeas = FEAS_TOLERANCE;
PREPROCESSING.OptFile = 1;

