*
* AUTHOR: Sascha Kuhnke
* Created: 21.03.2019
*

SETS
	
	UN				units
	UN_OUT(UN)		units with outlet flow
	UN_IN(UN)		units with inlet flow
	WS(UN)			water sources
	PL(UN)	 		pools
	WD(UN)			water demands
	CO				contaminants;	

$if not set gdxincname $abort 'No include file name for data file provided'
$gdxin %gdxincname%
$load UN UN_OUT UN_IN WS PL WD CO


PARAMETERS

* General
	FL_MAX_UN(UN)			maximum capacity at unit
	FL_MAX(UN, UN)			maximum capacity at pipe
	COST(UN, UN)			cost for pipe usage
	
* Water Sources
	PO_WS(WS, CO)			contaminant concentration leaving source	

* Water Demands
	PO_MIN_WD(WD, CO)		minimum allowed contaminant concentration	
	PO_MAX_WD(WD, CO)		maximum allowed contaminant concentration
	
* Preprocessing
	IS_ACTIVE_MIN(WD, CO)	states if the spec requirement constraints is active or removed 
	IS_ACTIVE_MAX(WD, CO)	states if the spec requirement constraints is active or removed;

$load FL_MAX_UN FL_MAX COST PO_WS PO_MIN_WD PO_MAX_WD IS_ACTIVE_MIN IS_ACTIVE_MAX


SCALARS

	ZERO					equals zero								/ 0 /
	ONE						equals one								/ 1 /
	FEAS_TOLERANCE			feasibility tolerance
	FEAS_TOLERANCE_CHECKER	feasibility tolerance for solution checker
	
	MODEL_STATUS			model solution status		
	SOLVE_STATUS			solver termination condition
	OBJEST					estimate of the best possible solution
	OBJVAL					objective function value;

$load FEAS_TOLERANCE FEAS_TOLERANCE_CHECKER
$gdxin


POSITIVE VARIABLES

* Flows
	FL(UN, WD)				flow in pipe
	FL_PR(WS, PL, WD)		flow from WS to WD via PL

* Proportions of Flow
	PR(WS, PL)				proportion of flow at pool coming from source;	


VARIABLE

	OBJ						objective function;



* Fix Variables at Water Demands
FL.Fx(WD, WD) = ZERO;


EQUATIONS

* General Constraints
	GE_FL_MAX_WS(WS) 
	GE_FL_MAX_PL(PL) 
	GE_FL_MAX_WD(WD) 
	GE_FL_MAX_PI(UN_OUT, WD)
	GE_FL_MAX_PI_PR(WS, PL)
	
* PQ-Formulation	
	PQ_PR_BALANCE(PL)
	PQ_FL_PR(WS, PL, WD)
	PQ_PO_MIN_WD(WD, CO)
	PQ_PO_MAX_WD(WD, CO)
	PQ_PO_MIN_WD_PP(WD, CO) 							
	PQ_PO_MAX_WD_PP(WD, CO)
	
	PQ_VALID_1(PL, WD) 
	PQ_VALID_2(WS, PL) 

* Objective Function
	OBJECTIVE;


* General Constraints
	GE_FL_MAX_WS(WS) ..				SUM(WD, FL(WS, WD)) + SUM((PL, WD), FL_PR(WS, PL, WD))	=L=		FL_MAX_UN(WS);
	GE_FL_MAX_PL(PL) ..				SUM(WD, FL(PL, WD))										=L=		FL_MAX_UN(PL);
	GE_FL_MAX_WD(WD) ..				SUM(UN_OUT, FL(UN_OUT, WD))								=L=		FL_MAX_UN(WD);
	GE_FL_MAX_PI(UN_OUT, WD) ..		FL(UN_OUT, WD)											=L=		FL_MAX(UN_OUT, WD);
	GE_FL_MAX_PI_PR(WS, PL) ..		SUM(WD, FL_PR(WS, PL, WD))								=L=		FL_MAX(WS, PL);
	
* PQ-Formulation	
	PQ_PR_BALANCE(PL) ..		SUM(WS, PR(WS, PL))				=E=		ONE;
	PQ_FL_PR(WS, PL, WD) ..		FL_PR(WS, PL, WD)				=E=		PR(WS, PL) * FL(PL, WD);
	PQ_PO_MIN_WD(WD, CO) ..		SUM(WS, PO_WS(WS, CO) * FL(WS, WD)) + SUM((WS, PL), PO_WS(WS, CO) * FL_PR(WS, PL, WD))	
								=G=		PO_MIN_WD(WD, CO) * (SUM(UN_OUT, FL(UN_OUT, WD)));
	PQ_PO_MAX_WD(WD, CO) .. 	SUM(WS, PO_WS(WS, CO) * FL(WS, WD)) + SUM((WS, PL), PO_WS(WS, CO) * FL_PR(WS, PL, WD))	
								=L=		PO_MAX_WD(WD, CO) * (SUM(UN_OUT, FL(UN_OUT, WD)));
	PQ_PO_MIN_WD_PP(WD, CO) ..	IS_ACTIVE_MIN(WD, CO) * (SUM(WS, PO_WS(WS, CO) * FL(WS, WD)) + SUM((WS, PL), PO_WS(WS, CO) * FL_PR(WS, PL, WD)))	
								=G=		IS_ACTIVE_MIN(WD, CO) * PO_MIN_WD(WD, CO) * (SUM(UN_OUT, FL(UN_OUT, WD)));
	PQ_PO_MAX_WD_PP(WD, CO) .. 	IS_ACTIVE_MAX(WD, CO) * (SUM(WS, PO_WS(WS, CO) * FL(WS, WD)) + SUM((WS, PL), PO_WS(WS, CO) * FL_PR(WS, PL, WD)))	
								=L=		IS_ACTIVE_MAX(WD, CO) * PO_MAX_WD(WD, CO) * (SUM(UN_OUT, FL(UN_OUT, WD)));								
	
	PQ_VALID_1(PL, WD) ..		SUM(WS, FL_PR(WS, PL, WD))		=E=		FL(PL, WD);
	PQ_VALID_2(WS, PL) ..		SUM(WD, FL_PR(WS, PL, WD))		=L=		FL_MAX_UN(PL) * PR(WS, PL); 

* Objective Function
	OBJECTIVE .. 			OBJ 	=E=	 	SUM((WS, WD), COST(WS, WD) * FL(WS, WD)) + 
											SUM((WS, PL, WD), (COST(WS, PL) + COST(PL, WD)) * FL_PR(WS, PL, WD));


MODEL

	PQ_FORMULATION / ALL - PQ_PO_MAX_WD - PQ_PO_MIN_WD /	
	PQ_CHECKER / ALL - PQ_PO_MAX_WD_PP - PQ_PO_MIN_WD_PP /;


OPTION

	threads = 1
	sysOut = ON;


PQ_FORMULATION.holdfixed = 1;
PQ_FORMULATION.tolInfeas = FEAS_TOLERANCE;
PQ_FORMULATION.OptFile = 1;

PQ_CHECKER.holdfixed = 1;
PQ_CHECKER.tolInfeas = FEAS_TOLERANCE_CHECKER;
PQ_CHECKER.OptFile = 1;

