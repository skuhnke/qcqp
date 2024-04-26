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
	CO				contaminants
	J				indices for discretization;	

$if not set gdxincname $abort 'No include file name for data file provided'
$gdxin %gdxincname%
$load UN UN_OUT UN_IN WS PL WD CO J


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
	IS_ACTIVE_MAX(WD, CO)	states if the spec requirement constraints is active or removed
	
* Discretization
	FRAC(PL, J)				proportion of inlet flow going to duplicate pool;	

$load FL_MAX_UN FL_MAX COST PO_WS PO_MIN_WD PO_MAX_WD IS_ACTIVE_MIN IS_ACTIVE_MAX


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

* Flows
	FL(UN, WD)					flow in pipe
	FL_PR(WS, PL, WD)			flow from WS to WD via PL

* Discretization
	FL_PR_DISC(WS, PL, J, WD)	auxiliary variables for discretization;

BINARY VARIABLES	
	
	CHI(PL, J, WD)				selection of discretized values;
	

VARIABLE

	OBJ							objective function;



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
	PQ_PO_MIN_WD(WD, CO)
	PQ_PO_MAX_WD(WD, CO)
	
* Discretization
	DISC_FL_PR(WS, PL, WD)
	DISC_FRAC_FL_PR(WS, PL, J)
	DISC_FL(PL, WD)
	
	DISC_FL_UP(WS, PL, J, WD)
	DISC_SOS(PL, J)

* Objective Function
	OBJECTIVE;


* General Constraints
	GE_FL_MAX_WS(WS) ..				SUM(WD, FL(WS, WD)) + SUM((PL, WD), FL_PR(WS, PL, WD))	=L=		FL_MAX_UN(WS);
	GE_FL_MAX_PL(PL) ..				SUM(WD, FL(PL, WD))										=L=		FL_MAX_UN(PL);
	GE_FL_MAX_WD(WD) ..				SUM(UN_OUT, FL(UN_OUT, WD))								=L=		FL_MAX_UN(WD);
	GE_FL_MAX_PI(UN_OUT, WD) ..		FL(UN_OUT, WD)											=L=		FL_MAX(UN_OUT, WD);
	GE_FL_MAX_PI_PR(WS, PL) ..		SUM(WD, FL_PR(WS, PL, WD))								=L=		FL_MAX(WS, PL);
	
* PQ-Formulation	
	PQ_PO_MIN_WD(WD, CO) ..			IS_ACTIVE_MIN(WD, CO) * (SUM(WS, PO_WS(WS, CO) * FL(WS, WD)) + SUM((WS, PL), PO_WS(WS, CO) * FL_PR(WS, PL, WD)))	
									=G=		IS_ACTIVE_MIN(WD, CO) * PO_MIN_WD(WD, CO) * (SUM(UN_OUT, FL(UN_OUT, WD)));
	PQ_PO_MAX_WD(WD, CO) .. 		IS_ACTIVE_MAX(WD, CO) * (SUM(WS, PO_WS(WS, CO) * FL(WS, WD)) + SUM((WS, PL), PO_WS(WS, CO) * FL_PR(WS, PL, WD)))	
									=L=		IS_ACTIVE_MAX(WD, CO) * PO_MAX_WD(WD, CO) * (SUM(UN_OUT, FL(UN_OUT, WD)));
	
* Discretization
	DISC_FL_PR(WS, PL, WD) ..		FL_PR(WS, PL, WD)						=E=		SUM(J, FL_PR_DISC(WS, PL, J, WD));
	DISC_FRAC_FL_PR(WS, PL, J) ..	SUM(WD, FL_PR_DISC(WS, PL, J, WD))		=E=		FRAC(PL, J) * SUM(WD, FL_PR(WS, PL, WD));
	DISC_FL(PL, WD) ..				FL(PL, WD)								=E=		SUM(WS, FL_PR(WS, PL, WD));
	
	DISC_FL_UP(WS, PL, J, WD) ..	FL_PR_DISC(WS, PL, J, WD)				=L=		FL_MAX(PL, WD) * CHI(PL, J, WD);
	DISC_SOS(PL, J) ..				SUM(WD, CHI(PL, J, WD)) 				=E= 	ONE;

* Objective Function
	OBJECTIVE .. 			OBJ 	=E=	 	SUM((WS, WD), COST(WS, WD) * FL(WS, WD)) + 
											SUM((WS, PL, WD), (COST(WS, PL) + COST(PL, WD)) * FL_PR(WS, PL, WD));


MODEL

	PQ_DISC_PL_DEY_GUPTE / ALL /;	


OPTION

	threads = 1
	sysOut = ON;


PQ_DISC_PL_DEY_GUPTE.holdfixed = 1;
PQ_DISC_PL_DEY_GUPTE.tolInfeas = FEAS_TOLERANCE;
PQ_DISC_PL_DEY_GUPTE.OptFile = 1;

