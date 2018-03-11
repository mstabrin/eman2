#!/usr/bin/env groovy

import groovy.json.JsonOutput
// Add whichever params you think you'd most want to have
// replace the slackURL below with the hook url provided by
// slack when you configure the webhook
def notifyGithub(state) {
    def githubURL = 'https://api.github.com/repos/cryoem/eman2/statuses'
    def payload = JsonOutput.toJson([state        : state,
                                     target_url   : "${BUILD_URL}",
                                     description  : "The build succeeded!",
                                     context      : "${JOB_NAME}"
                                     ])
    sh "curl -u eman-bot -X POST --data-urlencode \'payload=${payload}\' ${githubURL}"
}

def getJobType() {
    def causes = "${currentBuild.rawBuild.getCauses()}"
    def job_type = "UNKNOWN"
    
    if(causes ==~ /.*TimerTrigger.*/)    { job_type = "cron" }
    if(causes ==~ /.*GitHubPushCause.*/) { job_type = "push" }
    if(causes ==~ /.*UserIdCause.*/)     { job_type = "manual" }
    if(causes ==~ /.*ReplayCause.*/)     { job_type = "manual" }
    
    return job_type
}

def notifyGitHub(status) {
    if(JOB_TYPE == "push") {
        if(status == 'PENDING') { message = 'Building...' }
        if(status == 'SUCCESS') { message = 'Build succeeded!' }
        if(status == 'FAILURE') { message = 'Build failed!' }
        if(status == 'ERROR')   { message = 'Build aborted!' }
        step([$class: 'GitHubCommitStatusSetter', contextSource: [$class: 'ManuallyEnteredCommitContextSource', context: "JenkinsCI/${JOB_NAME}"], statusResultSource: [$class: 'ConditionalStatusResultSource', results: [[$class: 'AnyBuildResult', message: message, state: status]]]])
    }
}

def notifyEmail() {
    if(JOB_TYPE == "push") {
        emailext(to: "$GIT_AUTHOR_EMAIL",  
                 subject: '[JenkinsCI/$PROJECT_NAME/push] ' + "($GIT_BRANCH_SHORT - ${GIT_COMMIT_SHORT})" + ' #$BUILD_NUMBER - $BUILD_STATUS!',
                 body: '''${SCRIPT, template="groovy-text.template"}''',
                 attachLog: true
                 )
    }
}

def isReleaseBuild() {
    return GIT_BRANCH ==~ /.*\/release.*/
}

def isContinuousBuild() {
    return GIT_BRANCH ==~ /.*\/master/
}

def stage_name_to_os(stage_name) {
    def result = ['centos6': 'linux',
                  'centos7': 'linux',
                  'mac':     'mac',
                  'win':     'win'
                  ]
    
    return result[stage_name]
}

def isRequestedBuildStage() {
    def buildStage = ['centos6': CI_BUILD_LINUX,
                      'centos7': CI_BUILD_LINUX,
                      'mac':     CI_BUILD_MAC,
                      'win':     CI_BUILD_WIN
                      ]
    
    return (stage_name_to_os(STAGE_NAME) == SLAVE_OS && (CI_BUILD == "1" || buildStage[STAGE_NAME] == "1"))
}

def isSimpleBuild() {
    def buildOS = ['linux': CI_BUILD_LINUX,
                   'mac':   CI_BUILD_MAC,
                   'win':   CI_BUILD_WIN
                  ]
    
    return (CI_BUILD != "1" && buildOS[SLAVE_OS] != "1")
}

def runJob() {
    sh 'bash ci_support/conda_build.sh recipes/eman'
    sh "bash ci_support/package.sh ${INSTALLERS_DIR} " + '${WORKSPACE}/ci_support/'
    testPackage()
    deployPackage()
}

def testPackage() {
    if(SLAVE_OS != 'win')
        sh "bash tests/test_binary_installation.sh ${INSTALLERS_DIR} eman2.${SLAVE_OS}.sh"
    else
        sh 'ci_support/test_wrapper.sh'
}

def deployPackage() {
    if(isContinuousBuild()) {
        if(SLAVE_OS != 'win')
            sh "rsync -avzh --stats ${INSTALLERS_DIR}/eman2.${SLAVE_OS}.sh ${DEPLOY_DEST}/eman2.${STAGE_NAME}.unstable.sh"
        else
            bat 'ci_support\\rsync_wrapper.bat'
    }
}

def getHomeDir() {
    def result = ''
    if(SLAVE_OS == "win") {
        result = "${USERPROFILE}"
    }
    else {
        result = "${HOME}"
    }
    
    return result
}

def repoConfig() {
    checkout([$class: 'GitSCM', branches: [[name: '*/*']], doGenerateSubmoduleConfigurations: false, extensions: [[$class: 'PruneStaleBranch'], [$class: 'CleanBeforeCheckout'], [$class: 'MessageExclusion', excludedMessage: '(?s).*\\[skip jenkins\\].*']], submoduleCfg: [], userRemoteConfigs: [[url: 'repo']]])
}

pipeline {
  agent {
    node { label 'jenkins-slave-1' }
  }
  
  options {
    disableConcurrentBuilds()
    timestamps()
  }
  
  environment {
    JOB_TYPE = getJobType()
    GIT_BRANCH_SHORT = sh(returnStdout: true, script: 'echo ${GIT_BRANCH##origin/}').trim()
    GIT_COMMIT_SHORT = sh(returnStdout: true, script: 'echo ${GIT_COMMIT:0:7}').trim()
    GIT_AUTHOR_EMAIL = sh(returnStdout: true, script: 'git log -1 --format="%ae"').trim()
    HOME_DIR = getHomeDir()
    INSTALLERS_DIR = '${HOME_DIR}/workspace/${STAGE_NAME}-installers'
    DEPLOY_DEST    = 'zope@ncmi.grid.bcm.edu:/home/zope/zope-server/extdata/reposit/ncmi/software/counter_222/software_136/'

    CI_BUILD       = sh(script: "! git log -1 | grep '.*\\[ci build\\].*'",       returnStatus: true)
    CI_BUILD_WIN   = sh(script: "! git log -1 | grep '.*\\[ci build win\\].*'",   returnStatus: true)
    CI_BUILD_LINUX = sh(script: "! git log -1 | grep '.*\\[ci build linux\\].*'", returnStatus: true)
    CI_BUILD_MAC   = sh(script: "! git log -1 | grep '.*\\[ci build mac\\].*'",   returnStatus: true)
  }
  
  stages {
    // Stages triggered by GitHub pushes
    stage('notify-pending') {
      steps {
        notifyGitHub('PENDING')
      }
    }
    
    stage('build') {
      when {
        expression { isSimpleBuild() }
      }
      
      parallel {
        stage('recipe') {
          steps {
            sh 'bash ci_support/build_recipe.sh'
          }
        }
        
        stage('no_recipe') {
          when {
            expression { SLAVE_OS != 'win' }
          }
          
          steps {
            sh 'source $(conda info --root)/bin/activate eman-deps-9 && bash ci_support/build_no_recipe.sh'
          }
        }
      }
    }
    
    stage('centos6') {
      when {
        expression { isRequestedBuildStage() }
      }
      
      steps {
        sh "bash ci_support/run_docker_build.sh cryoem/centos6:8 . ${INSTALLERS_DIR}"
        deployPackage()
      }
    }
    
    stage('centos7') {
      when {
        expression { isRequestedBuildStage() }
      }
      
      steps {
        runJob()
      }
    }
    
    stage('mac') {
      when {
        expression { isRequestedBuildStage() }
      }
      environment {
        EMAN_TEST_SKIP=1
      }
      
      steps {
        runJob()
      }
    }
    
    stage('win') {
      when {
        expression { isRequestedBuildStage() }
      }
      
      steps {
        runJob()
      }
    }
  }
  
  post {
        always {
          archive "${HOME}/workspace/*-installers/*.*"
        }
        
    success {
      notifyGitHub('SUCCESS')
    }
    
    failure {
      notifyGitHub('FAILURE')
    }
    
    aborted {
      notifyGitHub('ERROR')
    }
    
    always {
      notifyEmail()
    }
  }
}
