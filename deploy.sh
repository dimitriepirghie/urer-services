#!/bin/bash

function deploy(){
    echo "Deploy started"
    for service in services/*
    do

        heroku_app_name="not setd"

        case "$service" in 
        *pois*)
            # Do stuff
                heroku_app_name="urer-pois-service"
            ;;
        *transportation*)
                heroku_app_name="urer-transportation-service"
            ;;

        *social*)
                heroku_app_name="urer-social-service"
            ;;    
        esac
         echo "Deploy $service at app $heroku_app_name"

         cd ./$service

         if [ -d ".git" ]; then
            echo "Warning existing git repo for deploy"
            rm -rf .git
         fi

         git init
         heroku git:remote -a $heroku_app_name
         echo "Add changes"
         git add .
         echo "Do commit"
         git commit -am "Automatic deploy to $heroku_app_name"
         echo "Push to heroku "
         git push -f heroku master

         rm -rf .git
         cd -

    done
}

function launch_services(){
       python services/pois_service/pois_app.py &> /dev/null &
       python services/social_service/social_app.py &> /dev/null &
       python services/transportation_service/transportation_app.py &> /dev/null &
}

function run_tests(){
    for file in tests/*.py
    do
        echo "Test: $file"
        python $file
        if [ $? -ne 0 ]; then
            return 1
        fi
    done
    return 0
}

function tests(){
    launch_services
    sleep 5
    run_tests

    if [ $? -ne 0 ]; then
        echo "Tests failed, deploy aborted"
        exit 1
    fi

    killall python
}

if [ $1==1 ];then
    echo "Runnig just tests"
    tests
else
    tests
    deploy
fi