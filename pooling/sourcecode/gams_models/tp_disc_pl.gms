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
	FL(WS, UN)					flow in pipe
	FL_PR(WS, PL, WD)			flow from WS to WD via PL

* Discretization
	FL_PR_DISC(WS, PL, J, WD)	auxiliary variables for discretization;

BINARY VARIABLES	
	
	CHI(PL, J, WD)				selection of discretized values;
	

VARIABLE

	OBJ							objective function;



* Fix Variables at Water Sources
FL.Fx(WS, WS) = ZERO;


EQUATIONS

* General Constraints
	GE_FL_MAX_WS(WS)
	GE_FL_MAX_PL(PL)
	GE_FL_MAX_WD(WD)
	GE_FL_MAX_PI(WS, UN_IN)
	GE_FL_MAX_PI_PR(PL, WD)
	
* TP-Formulation	
	TP_PO_MIN_WD(WD, CO)
	TP_PO_MAX_WD(WD, CO)

	TP_VALID_1(WS, PL)
	
* Discretization
	DISC_FL_PR(WS, PL, WD)
	DISC_FRAC_FL_PR(WS, PL, J)
	
	DISC_FL_UP(PL, J, WD)
	DISC_SOS(PL, J)

* Objective Function
	OBJECTIVE;


* General Constraints
	GE_FL_MAX_WS(WS) ..				SUM(UN_IN, FL(WS, UN_IN))								=L=		FL_MAX_UN(WS);
	GE_FL_MAX_PL(PL) ..				SUM(WS, FL(WS, PL))										=L=		FL_MAX_UN(PL);
	GE_FL_MAX_WD(WD) ..				SUM(WS, FL(WS, WD)) + SUM((WS, PL), FL_PR(WS, PL, WD)) 	=L=		FL_MAX_UN(WD);
	GE_FL_MAX_PI(WS, UN_IN) ..		FL(WS, UN_IN)											=L=		FL_MAX(WS, UN_IN);
	GE_FL_MAX_PI_PR(PL, WD) ..		SUM(WS, FL_PR(WS, PL, WD))								=L=		FL_MAX(PL, WD);
	
* TP-Formulation	
	TP_PO_MIN_WD(WD, CO) ..			IS_ACTIVE_MIN(WD, CO) * (SUM(WS, PO_WS(WS, CO) * FL(WS, WD)) + SUM((WS, PL), PO_WS(WS, CO) * FL_PR(WS, PL, WD)))
									=G=		IS_ACTIVE_MIN(WD, CO) * PO_MIN_WD(WD, CO) * (SUM(WS, FL(WS, WD)) + SUM((WS, PL), FL_PR(WS, PL, WD)));
	TP_PO_MAX_WD(WD, CO) .. 		IS_ACTIVE_MAX(WD, CO) * (SUM(WS, PO_WS(WS, CO) * FL(WS, WD)) + SUM((WS, PL), PO_WS(WS, CO) * FL_PR(WS, PL, WD)))
									=L=		IS_ACTIVE_MAX(WD, CO) * PO_MAX_WD(WD, CO) * (SUM(WS, FL(WS, WD)) + SUM((WS, PL), FL_PR(WS, PL, WD)));
	
	TP_VALID_1(WS, PL) ..			SUM(WD, FL_PR(WS, PL, WD))		=E=		FL(WS, PL);

* Discretization
	DISC_FL_PR(WS, PL, WD) ..		FL_PR(WS, PL, WD)					=E=		SUM(J, FL_PR_DISC(WS, PL, J, WD));
	DISC_FRAC_FL_PR(WS, PL, J) ..	SUM(WD, FL_PR_DISC(WS, PL, J, WD))	=E=		FRAC(PL, J) * FL(WS, PL);
	
	DISC_FL_UP(PL, J, WD) ..		SUM(WS, FL_PR_DISC(WS, PL, J, WD))	=L=		MIN(FRAC(PL, J) * FL_MAX_UN(PL), FL_MAX(PL, WD)) * CHI(PL, J, WD);
	DISC_SOS(PL, J) ..				SUM(WD, CHI(PL, J, WD)) 			=E= 	ONE;

* Objective Function
	OBJECTIVE .. 			OBJ 	=E=	 	SUM((WS, WD), COST(WS, WD) * FL(WS, WD)) + 
											SUM((WS, PL, WD), (COST(WS, PL) + COST(PL, WD)) * FL_PR(WS, PL, WD));


MODEL

	TP_DISC_PL / ALL /;	


OPTION

	threads = 1
	sysOut = ON;


TP_DISC_PL.holdfixed = 1;
TP_DISC_PL.tolInfeas = FEAS_TOLERANCE;
TP_DISC_PL.OptFile = 1;

