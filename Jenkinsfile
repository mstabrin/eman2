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
                 subject: '[JenkinsCI/$PROJECT_NAME] ' + "($GIT_BRANCH_SHORT - ${GIT_COMMIT_SHORT})" + ' #$BUILD_NUMBER - $BUILD_STATUS!',
                 body: '''${SCRIPT, template="groovy-text.template"}''',
                 attachLog: true
                 )
    }
}

def isReleaseBuild() {
    return GIT_BRANCH ==~ /.*\/release.*/
}

def isBinaryBuild() {
    def buildOS = ['linux': CI_BUILD_LINUX,
                   'mac':   CI_BUILD_MAC,
                   'win':   CI_BUILD_WIN
                  ]
    
    return (CI_BUILD == "1" || buildOS[SLAVE_OS] == "1")
}

def testPackage() {
    if(SLAVE_OS != 'win')
        sh "bash tests/test_binary_installation.sh ${INSTALLERS_DIR} eman2.${SLAVE_OS}.sh"
    else
        sh 'ci_support/test_wrapper.sh'
}

def deployPackage() {
    def installer_base_name = ['Centos6': 'centos6',
                               'Centos7': 'centos7',
                               'MacOSX' : 'mac',
                              ]
    if(CI_BUILD) {
        upload_dir = 'continuous_build'
        upload_ext = 'unstable'
    }
    if(CI_BUILD_EXP) {
        upload_dir = 'experimental'
        upload_ext = 'experimental'
    }
    
    if(isBinaryBuild()) {
        if(SLAVE_OS != 'win')
            sh "rsync -n -avzh --stats ${INSTALLERS_DIR}/eman2.${SLAVE_OS}.sh ${DEPLOY_DEST}/" + upload_dir + "/eman2." + installer_base_name[JOB_NAME] + "." + upload_ext + ".sh"
        else
            bat 'ci_support\\rsync_wrapper.bat ' + upload_dir + ' ' + upload_ext
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

pipeline {
  agent {
    node { label "${JOB_NAME}-slave" }
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
    INSTALLERS_DIR = '${HOME_DIR}/workspace/${JOB_NAME}-installers'

    CI_BUILD       = sh(script: "! git log -1 | grep '.*\\[ci build\\].*'",       returnStatus: true)
    CI_BUILD_WIN   = sh(script: "! git log -1 | grep '.*\\[ci build win\\].*'",   returnStatus: true)
    CI_BUILD_LINUX = sh(script: "! git log -1 | grep '.*\\[ci build linux\\].*'", returnStatus: true)
    CI_BUILD_MAC   = sh(script: "! git log -1 | grep '.*\\[ci build mac\\].*'",   returnStatus: true)
    CI_BUILD_EXP   = sh(script: "! git log -1 | grep '.*\\[ci build exp\\].*'",   returnStatus: true)
  }
  
  stages {
    // Stages triggered by GitHub pushes
    stage('notify-pending') {
      steps {
        notifyGitHub('PENDING')
        sh 'env | sort'
      }
    }
    
    stage('build-local') {
      when {
        not { expression { isBinaryBuild() } }
        expression { JOB_NAME != 'Win' }
      }
      
      steps {
        echo 'source $(conda info --root)/bin/activate eman-deps-9 && bash ci_support/build_no_recipe.sh'
      }
    }
    
    stage('build-recipe') {
      steps {
        echo 'bash ci_support/build_recipe.sh'
      }
    }
    
    stage('package') {
      when {
        expression { isBinaryBuild() }
      }
      
      steps {
        echo "bash ci_support/package.sh ${INSTALLERS_DIR} " + '${WORKSPACE}/ci_support/'
      }
    }
    
    stage('test-package') {
      when {
        expression {isBinaryBuild() }
      }
      
      steps {
        echo 'testPackage()'
      }
    }
    
    stage('deploy') {
      when {
        expression {isBinaryBuild() }
      }
      
      steps {
        deployPackage()
      }
    }
  }
  
  post {
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
