pipeline {
    options {
        parallelsAlwaysFailFast()
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }

    environment {
        PROJECT = 'data-template'
        CHANNEL = '#test-slack-notif'
        IMAGE = 'juvo/data-template'
    }

    agent {
        kubernetes {
            label 'jenkins-data'
            yaml libraryResource('pod_templates/data_agent_dind.yaml')
            defaultContainer 'jenkins-agent-data'
        }
    }

    stages {
        stage('Start') {
            steps {
                sendStartBuildNotification(env.CHANNEL)
                checkout scm
                script {
                    env.HASH = getGitCommitHash()
                    env.TAG = buildDockerTag(env.BRANCH_NAME, env.HASH)
                    currentBuild.description = env.imageTag
                }
            }
        }
        stage('Sniff') {
            parallel {
                stage('Lint') {
                    steps {
                        sh "flake8 ."
                    }
                }
                stage('Type Checking') {
                    steps {
                        sh "mypy ."
                    }
                }
                stage('Static Analysis') {
                    steps {
                        withSonarQubeEnv('SonarQube') {
                            sh "sonar-scanner -Dsonar.host.url=${SONAR_HOST_URL} -Dsonar.projectKey=${PROJECT}"
                        }
                    }
                }
                stage('Build') {
                    stages {
                        stage('Build') {
                            steps {
                                buildDockerContainer(env.IMAGE, env.TAG)
                            }
                        }
                        stage('Test') {
                            steps {
                                sh "docker run --entrypoint /bin/bash ${IMAGE}:${TAG} -c 'pip install ./${PROJECT}[test]; pytest'"
                            }
                        }
                    }
                }
            }
        }
        stage('Push') {
            when {
                branch "master"
            }
            steps {
                pushDockerContainer(env.IMAGE, env.TAG)
            }
        }
    }

    post {
        failure {
            sendEndBuildNotification(currentBuild.currentResult, env.CHANNEL, '')
        }
        success {
            sendEndBuildNotification(currentBuild.currentResult, env.CHANNEL, "Built docker image ${IMAGE}:${TAG}")
        }
    }
}
