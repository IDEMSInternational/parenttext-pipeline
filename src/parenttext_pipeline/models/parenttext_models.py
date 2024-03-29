from rpft.parsers.creation.datarowmodel import DataRowModel
from rpft.parsers.common.rowparser import ParserModel
from typing import List

###################################################################
class IntroductionBlockModel(ParserModel):
	msg_list: List[str] = []

class ImportanceBlockModel(ParserModel):
	msg_list: List[str] = []

class QuizContentModel(ParserModel):
	question: List[str] = []
	image: str = ''
	values: List[str] = []
	answer: str = ''
	feedback_correct: List[str] = []
	feedback_incorrect: List[str] = []

class QuizBlockModel(ParserModel):
	intro: str = ''
	content: List[QuizContentModel] = []

class TipModel(ParserModel):
	text: List[str] = []
	image: str = ''

class TipsBlockModel(ParserModel):
	intro: str = ''
	next_button: str = ''
	message: List[TipModel] = []

class ComicBlockModel(ParserModel):
	intro: str = ''
	file_name: str = ''
	n_attachments: str = ''
	next_button: str = ''
	text: List[str] = []

class HomeActivityBlockModel(ParserModel):
	intro: List[str] = []
	activity: str = ''
	positive_msg: str = ''
	negative_msg: str = ''

class CongratulationsBlockModel(ParserModel):
	msg_list: List[str] = []


class VideoBlockModel(ParserModel):
	script: str = ''
	message: str = ''
	file_name: str = ''
	expiration_time_min: str = ''


class AudioBlockModel(ParserModel):
	message: str = ''
	file_name: str = ''
	expiration_time_min: str = ''

class OptVideoBlockModel(ParserModel):
	query: str = ''
	yes_opt: str = ''
	no_opt: str = ''
	intro: str = ''
	no_msg: str = ''


class PlhContentModel(DataRowModel):
	module_name: str = ''
	pause_id: str = ''
	introduction: IntroductionBlockModel = IntroductionBlockModel()
	importance: ImportanceBlockModel = ImportanceBlockModel()
	quiz: QuizBlockModel = QuizBlockModel()
	tips: TipsBlockModel = TipsBlockModel()
	comic: ComicBlockModel = ComicBlockModel()
	home_activity: HomeActivityBlockModel = HomeActivityBlockModel()
	video: VideoBlockModel = VideoBlockModel()
	audio: AudioBlockModel = AudioBlockModel()
	congratulations: CongratulationsBlockModel = CongratulationsBlockModel()
	opt_video: OptVideoBlockModel = OptVideoBlockModel()
	attached_single_doc: str = ''


class TrackerInfoModel(ParserModel):
	name: str = ''
	tracker_tot: str = ''
	has_tracker: str = ''

class FlowStructureModel(DataRowModel):
	block: List[TrackerInfoModel] = []


class BlockMetadataModel(DataRowModel):
	include_if_cond: str = ''
	args: str = ''


#######
##demo
class ShortDemoModel(DataRowModel):
	onb_qst: List[str] = []

#########################################################
##goal check in

class TroubleModel(ParserModel):
	pb: str = ''
	tip: List[str] = []

class TroubleshootingModel(DataRowModel):
	question: str = ''
	problems: List[TroubleModel] = []

class GoalCheckInResponseModel(DataRowModel):
	pre_goal_positive: str = ''
	pre_goal_negative: str = ''
	post_goal_improved_positive: str = ''
	post_goal_improved_negative: str = ''
	post_goal_static_positive: str = ''
	post_goal_static_negative: str = ''
	post_goal_worsened_positive: str = ''
	post_goal_worsened_negative: str = ''

class GoalCheckInModel(DataRowModel):
	intro_pre_goal: str = ''
	intro_post_goal: str = ''
	pre_question: str = ''
	question: str = ''
	options: List[str] = []
	skip_option: str = '' 
	add_qr: str = ''
	negative: List[str] = []
	positive: List[str] = []
	improvement: str = ''
	response: GoalCheckInResponseModel = GoalCheckInResponseModel()
	post_goal_positive_follow_up_question: str = ''
	post_goal_positive_follow_up_options: List[str] = []
	follow_up_positive_options: List[str] = []
	follow_up_negative_options: List[str] = []
	follow_up_positive_message: str = ''
	follow_up_negative_message: str = ''
	troubleshooting: TroubleshootingModel = TroubleshootingModel()
	conclusion: str = ''
	attached_single_doc: str = ''

class PbSurveyBehaveModel(ParserModel):
	name: str = ''
	post_goal_msg: str = ''

class SurveyBehaveModel(DataRowModel):
	intro: str = ''
	select_instructions: str = ''
	pb: List[PbSurveyBehaveModel] = []
	attached_single_doc: str = ''
###########################################################
# onboarding

class OnboardingStepsModel(DataRowModel):
	flow: str = ''
	variable: str = ''

class OnboardingQuestionOptionModel(ParserModel):
	text: str = ''
	value: str = ''
	alias: str = ''

class OnboardingQuestionWithOptionsModel(DataRowModel):
	question: str = ''
	image: str = ''
	variable: str = ''
	completion_variable: str = ''
	back_option: str = ''
	back_flow: str = ''
	options : List[OnboardingQuestionOptionModel] = []
	attached_single_doc: str = ''

class OnboardingQuestionInputTestModel(ParserModel):
	expression: str = ''
	value: str = ''
	condition_type: str = ''

class OnboardingQuestionInputModel(DataRowModel):
	question: str = ''
	variable: str = ''
	skip_option: str = ''
	skip_value: str = ''
	test: OnboardingQuestionInputTestModel = OnboardingQuestionInputTestModel()
	error_message: str = ''
	attached_single_doc: str = ''

class OnboardingRangeModel(ParserModel):
	limit: str = ''
	var_value: str = ''

class OnboardingQuestionRangeModel(DataRowModel):
	question: str = ''
	variable: str = ''
	grouping_variable: str = ''
	lower_bound: int = 0
	low_error_msg: str = ''
	upper_bound: int = 0
	up_error_msg: str = ''
	general_error_msg: str = ''
	ranges: List[OnboardingRangeModel] = []

################################
## LTP activity
class LtpActivityModel (DataRowModel):
	name: str = ''
	text: str = ''
	act_type: List[str] = ["Active"] #???
	act_age: List[int] = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17] 
	use_in_demo: str = ''
	attached_single_doc: str = ''
################################
## home activity check-in

class HomeActivityCheckInModel(DataRowModel):
	activity: str = ''
	positive_message: str = ''
	negative_message: str = ''
	attached_single_doc: str = ''

class WhatsappTemplateModel(DataRowModel):
	name: str = ''
	uuid: str = ''
	text: str = ''

#########################
## dev assessment tools
class WgUnicefModel(DataRowModel):
	intro: str = ''
	end_message_concerning: List[str] = []
	end_message_not_concerning: List[str] = []
	questions_ids: List[str] = []
	attached_single_doc: str = ''

class WgUnicefQuestionModel(DataRowModel):
	qst: str = ''
	options: List[str] = []
	concerning_options: List[str] = []
	concerning_feedback: str = ''
	attached_single_doc: str = ''

class SwycModel(DataRowModel):
	intro: List[str] = []
	options: List[str] = []
	scores: List[int] = []
	threshold_age: List[int] = []
	threshold_score: List[int] = []
	end_message_concerning: List[str] = []
	end_message_not_concerning: List[str] = []
	questions: List[str] = []
	attached_single_doc: str = ''

#########################
## delivery

class VariableModel(DataRowModel):
	name: str = ''
	value: str = '' 

class IdGeneratorModel(DataRowModel):
    success_msg: str = ''
    failure_msg: str = ''

class WebhookSettingsModel(DataRowModel):
    url: str = ''
    token: str = ''

class RangeProgDataModel(ParserModel):
	limit: str = ''
	value: str = ''

class ProgDataModel(DataRowModel):
	ranges: List[RangeProgDataModel] = []

class SplitModel(DataRowModel):
	split_variable: str = ''
	flow_name: str = ''
	text_name: str = ''
	nested: str = ''


class ModuleModel(DataRowModel):
	module_name: str = ''
	age_baby: bool = True
	age_child: bool = True
	age_teen: bool = True

class HandlerWrapperModel(DataRowModel):
	pre_update_flow: str = ''
	handler_flow: str = ''
	post_update_flow: str = ''

class OptionsWrapperOneOptionModel(ParserModel):
	message: str = ''
	question: str = ''
	affirmative: str = ''
	negative: str = ''
	no_message: str = ''

class OptionsWrapperNoOptionModel(ParserModel):
	message: str = ''
	image: str = ''

class OptionsWrapperModel(DataRowModel):
	list_var: str = ''
	print_type: str = ''
	n_max_opt: int = 10
	msg_no_options: OptionsWrapperNoOptionModel = OptionsWrapperNoOptionModel()
	msg_one_option: OptionsWrapperOneOptionModel = OptionsWrapperOneOptionModel()
	msg_multiple_options: str = ''
	select_instructions: str = ''
	extra_option: str = ''
	extra_message: str = ''
	update_var: str = ''
	update_var_flow: str = ''
	dict_ID: str = ''


class ProceedModel(ParserModel):
	question: str = ''
	yes_opt: str = ''
	no_opt: str = ''
	no_msg: str = ''


class SelectGoalModel(DataRowModel):
	update_prog_var_flow: str = ''
	split_by_goal_update_flow: str = ''
	goal_description: str = ''	
	proceed: ProceedModel = ProceedModel()

class InteractionOptionModel(ParserModel):
	text: str = ''
	proceed_result_value: str = ''
	stop_message: str = ''

class InteractionModel(DataRowModel):
	question: str = ''
	options: List[InteractionOptionModel] = []
	webhook_template_name: str = ''
	webhook_template_args: str = ''
	wa_template_ID: str = ''
	wa_template_vars: List[str] = []



class TimedProgrammeModel(DataRowModel):
	completion_variable: str = ''
	incomplete_value: str = ''
	incomplete_test: str = ''
	incomplete_name: str = ''
	interaction_flow: str = ''
	interaction_proceed_value: str = ''
	flow: str = ''


class ActivityTypeModel(DataRowModel):
	option_name: str = ''

class AgeGroupModel(ParserModel):
    baby: str = ''
    child: str = ''
    teen: str = ''
	
class ActivityOfferModel(DataRowModel):
	activity_handler_flow: str = ''
	offer_msg: str = ''
	accept: AgeGroupModel = AgeGroupModel()
	refuse: str = ''
	refuse_msg: str = ''
	next_offer_msg: str = ''
	next_accept: str = ''
	next_refuse: str = ''
	next_refuse_msg: str = ''
	next_refuse_flow: str = ''
	next_other_opt: str = ''
	next_other_msg: str = ''
	next_other_flow: str = ''

class ComicNamesModel(DataRowModel):
	names: List[str] = []

class DictionaryModel(DataRowModel):
	languages: List[str] = []
	attached_single_doc: str = ''

class UseDictionaryModel(DataRowModel):
	dict_name: str = ''
	N: str = ''
	key: str = ''


class CongratsDataModel(DataRowModel):
	msg: str = ''
	extra_msg: str = ''

class MetadataModel(ParserModel):
    description: str = ''

class SingleMessageModel(DataRowModel):
	msg: str = ''
	next_button_option: str = ''
	metadata: MetadataModel = MetadataModel()

####################################
## Menu
class MenuOptionModel(ParserModel):
	text: str = ''
	flow: str = ''
	
class MessageMenuModel(ParserModel):
	text: str = ''
	image: str = ''
	

class MenuModel(DataRowModel):
	message: MessageMenuModel = MessageMenuModel()
	return_option: MenuOptionModel = MenuOptionModel()
	exit_option: MenuOptionModel = MenuOptionModel()
	options: List[MenuOptionModel] = []

class MenuBlocksModel(ParserModel):
	no_opt: str = ''
	one_opt: str = ''
	mult_opt: str = ''

class MenuProgressModel(DataRowModel):
	show_options_id: str = ''
	menu_blocks: MenuBlocksModel = MenuBlocksModel()

class SelectGoalMenuModel(DataRowModel):
	type: str = ''

class MissingProfileModel(ParserModel):
	msg: str = ''
	value: str = ''	

class VarProfileModel(ParserModel):
	val: str = ''
	alias: str = ''
	
class SettingsProfileModel(DataRowModel):
	current_info_msg: str = ''
	missing: MissingProfileModel = MissingProfileModel()
	update_inquiry: str = ''
	update_var_flow: str = ''
	confirmation_msg: str = ''
	update_prog_var_flow: str = ''
	variable: str = ''
	var: List[VarProfileModel] = []
	attached_single_doc: str = ''
											
####################################
## Safeguarding

class ReferralsModel(DataRowModel):
	referrals: str = ''
	option_name: str = ''


class SafeguardingRedirectModel(DataRowModel):
	flow: str = ''
	expiration_msg: str = ''
	kw_type: str = ''
	enabled: str = ''
	proceed: str = ''

class SafeguardingEntryModel(DataRowModel):
	question: str = ''
	yes_opt: str = ''
	yes_aliases: str = ''
	no_opt: str = ''
	no_aliases: str = ''
	intro: str = ''
	no_message: str = ''


class UpdateVarModel(ParserModel):
	name: str = ''
	value: str = ''

class SafeguardingLaunchFlowModel(DataRowModel):
	var: UpdateVarModel = UpdateVarModel()
	disabled_not_completed_registration: str = ''
	disabled_not_selected_first_goal: str = ''
	conclusion_msg: str = ''
	expiration_msg: str = ''
	flow: str = '' #backward compatibility


# content delivery data models (to be amended when new languages are required)
class Language(ParserModel):
    eng: str = ""
    msa: str = ""
    zho: str = ""
    spa: str = ""
    fra: str = ""

class GoalDataModel(DataRowModel):
    priority_c: str = ""
    priority_t: str = ""
    priority_p: str = ""
    relationship: List[str] = []
    checkin_c: str = ""
    checkin_t: str = ""
    name_c: Language = Language()
    name_t: Language = Language()



class ModuleDataModel(DataRowModel):
    topic_ID: str = ""
    priority_in_topic: str = ""
    age: List[int] = []
    child_gender: List[str] = []
    name_c: Language = Language()
    name: Language = Language()

class GoalTopicLinkModel(DataRowModel):
    goal_id_c: str = ""
    goal_id_t: str = ""
    goal_id_p: str = ""
    priority_in_goal_c: str = ""
    priority_in_goal_p: str = ""
    priority_in_goal_t: str = ""
