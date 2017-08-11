import sammy as sm


sam = sm.SAM(Description='Alexa Skill https://developer.amazon.com/alexa-skills-kit')

sam.add_resource(sm.Function(
    name='AlexaSkillFunction',
    CodeUri='s3://<bucket>/alexa_skill.zip',
    Handler='index.handler',
    Runtime='nodejs4.3',
    Events=[sm.AlexaSkillEvent(name='AlexaSkillEvent')]
))
