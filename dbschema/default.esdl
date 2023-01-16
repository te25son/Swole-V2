module default {
    abstract type Owned {
        required link user -> User {
            on target delete delete source;
        }
    }

    type User {
        required property username -> str {
            constraint exclusive;
        }
        required property hashed_password -> str;
        property email -> str;
        property disabled -> bool;

        multi link workouts := .<user[is Workout];
        multi link exercises := .<user[is Exercise];
    }

    type Workout extending Owned {
        required property name -> str;
        required property date -> cal::local_date;

        multi link exercises := .<workouts[is Exercise];

        constraint exclusive on ((.name, .date, .user));
    }

    type Exercise extending Owned {
        required property name -> str;

        multi link workouts -> Workout {
            on target delete allow;
        }
        multi link sets := .<exercise[is ExerciseSet];

        constraint exclusive on ((.name, .user));
    }

    type ExerciseSet {
        required property weight -> positive_int {
            constraint max_value(10000);
        }
        required property rep_count -> positive_int {
            constraint max_value(500);
        }

        required link exercise -> Exercise {
            on target delete delete source;
        }
        required link workout -> Workout {
            on target delete delete source;
        }
    }

    # Custom Scalars
    scalar type positive_int extending int64 {
        constraint min_ex_value(0);
    }
}
