s/\{@\s*?(\S+)\s*?!=\s*?\\\"\\\"\s*?@\}/{@ \1 is defined and \1 != '' @}/
s/\{@\s*?(\S+)\s*?!=\s*?\\\"\\\"\s*?and\s*?(\S+)\s*?!=\s*?\\\"\\\"\s*?@\}/{@ \1 is defined and \1 != '' and \2 is defined and \2 != '' @}/
s/\{%\s*?if (\S+)\s*?!=\s*?\\\"\\\"\s*?%\}/{% if \1 is defined and \1 != '' %}/g
s/\{%\s*?if (\S+)\s*?==\s*?\\\"\\\"\s*?%\}/{% if not \1 %}/g
s/\{@\s*?(\S+)\s*?==\s*?\\\"\\\"\s*?@\}/{@ not \1 @}/
s/(congratulations|importance|introduction)\.msg_list\":/\1.msg_list.1":/
s/tips\.message\.([0-9])\.text\":/tips.message.\1.text.1":/
s/\{@tip_msg\.text\|length>0@\}/{@ tip_msg.text | select('ne', '') | list | length > 0 @}/
/\"ltp_activity\":/,/message_text/ s/\{\{text\}\}/{@ text @}/