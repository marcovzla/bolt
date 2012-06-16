(load "/Users/pcohen/Paul's Files/Mylisp/statistics.lisp")
(in-package :statistics)
(load "/Users/pcohen/Paul's Files/Contracts/Mind's Eye/R stuff/Data and Code/Pose/April 24/m-read-and-write.lisp")

(defparameter *table* 100)

(defun in-region? (loc p)
  "This returns t or nil depending on whether loc probabilistically falls in
a region defined by probability p.  For example, if p = .1, then we drape a
binomial with p = .1 over the table and find the area A less than or equal to loc.  
Then we return T with probability A. For example, the probability of T given that
loc = 10% of the length of the table is roughly 0.42 when p = .1. This jumps to .88 
when p = .15.  So we can use p to adjust the probability of calling a given region
of the table extreme."  
    (> (random 1.0) (binomial-le-probability *table* loc p)))

(defun which-region? (loc)
  (cond ((in-region? loc .15) 'extreme)
        ((in-region? loc .25) 'moderate)
        (t 'middle)))

(defun which-end? (loc)
  (if (> loc (/ *table* 2)) 'far 'near))

(defun very-near-center? (loc &optional (threshold (/ *table* 20)))
  (< (abs (- loc (/ *table* 2))) threshold))

(defun very-near-end? (loc &optional (threshold (/ *table* 17)))
  (or  (< loc threshold)(< (- *table* loc) threshold)))

(defun pick-a-phrase (phrases)
  (elt phrases (random (length phrases))))

(defun pick-a-word (words)
  (elt words (random (length words))))

(defun pick-phrase (loc)
 (let* ((t2 (/ *table* 2))
        (loc1  (- t2 (abs (- loc t2))))
        (region (which-region? loc1))
        (near (< loc t2))
        (far (> loc t2))
        (precise (> (random 1.0) .25))
        )
   (list
    loc region (if near 'near 'far) precise 
    (cond  ((and precise (very-near-center? loc))
           (pick-a-phrase (list (format nil "at the ~a of the table" 
                                        (pick-a-word (list "middle" "center")))
                                (format nil "in the ~a of the table" 
                                        (pick-a-word (list "middle" "center")))
                                (format nil "very near the ~a of the table" 
                                        (pick-a-word (list "middle" "center"))))))                                     
                               
          ((and precise (equal region 'middle)(not (very-near-center? loc)))
           (pick-a-phrase (list (format nil "near the ~a of the table" 
                                        (pick-a-word (list "middle" "center")))
                                (format nil "close to the ~a of the table" 
                                        (pick-a-word (list "middle" "center")))
                                (format nil "toward the ~a of the table" 
                                        (pick-a-word (list "middle" "center")))
                                (format nil "not far from the ~a of the table" 
                                        (pick-a-word (list "middle" "center"))))))
          
          ((and precise far (equal region 'moderate))
           (pick-a-phrase (list "down the table"
                                (format nil "~a ~a end of the table" 
                                        (pick-a-word (list "close to" "not far from" "near"))
                                        (pick-a-word (list "the far" "that" "the other")))
                                (format nil "past the ~a of the table" 
                                        (pick-a-word (list "middle" "center")))
                                (format nil "on the other side of the ~a of the table" 
                                        (pick-a-word (list "middle" "center"))))))

          ((and precise near (equal region 'moderate))
           (pick-a-phrase (list (format nil "~a ~a end of the table" 
                                        (pick-a-word (list "close to" "not far from" "near"))
                                        (pick-a-word (list "this" "my")))
                                (format nil "not past the ~a of the table" 
                                        (pick-a-word (list "middle" "center")))
                                (format nil "closer ~a than the ~a of the table" 
                                        (pick-a-word (list "to me" ""))
                                        (pick-a-word (list "middle" "center")))
                                (format nil "on ~a side of the ~a of the table" 
                                        (pick-a-word (list "my" "this"))
                                        (pick-a-word (list "middle" "center"))))))
          
          ((and precise far (very-near-end? loc))
           (pick-a-phrase (list (format nil "~a ~a end of the table" 
                                        (pick-a-word (list "at" "on"))
                                        (pick-a-word (list "that" "the other" "the far"))))))
          ((and precise far (equal region 'extreme))
           (pick-a-phrase (list (format nil "~a ~a end of the table" 
                                        (pick-a-word (list "very near" "very close to" "nearly at"))
                                        (pick-a-word (list "that" "the other" "the far"))))))

          ((and precise near (very-near-end? loc))
           (pick-a-phrase (list (format nil "~a ~a end of the table" 
                                        (pick-a-word (list "at" "on"))
                                        (pick-a-word (list "this" "my" "the near"))))))
          ((and precise near (equal region 'extreme))
           (pick-a-phrase (list (format nil "~a ~a end of the table" 
                                        (pick-a-word (list "very near" "very close to" "nearly at"))
                                        (pick-a-word (list "this" "my" "the near"))))))

          ((and (not precise) (equal region 'middle))
           (pick-a-phrase (list 
                           "on the table"
                           (format nil "near the ~a of the table" 
                                   (pick-a-word (list "middle" "center")))
                           (format nil "around the ~a of the table" 
                                   (pick-a-word (list "middle" "center")))
                           (format nil "not far from the ~a of the table" 
                                   (pick-a-word (list "middle" "center"))))))
          
          ((and (not precise) (equal region 'moderate))
           (pick-a-phrase (list "on the table"
                                (format nil "~a ~a end of the table" 
                                        (pick-a-word (list "toward" "not far from" "near"))
                                        (pick-a-word (list "the"))))))

          ((and (not precise) (equal region 'extreme))
           (pick-a-phrase (list (format nil "~a ~a end of the table" 
                                        (pick-a-word (list "very near" "very close to" "nearly at"))
                                        (pick-a-word (list "the"))))))
          ))))


(write-csv-to-file 
 "/Users/pcohen/Paul's Files/Contracts/BOLT/Data/Prepositions May 31 2012/sentences.csv"
 (append (list '(location region nearfar precise phrase))
         (loop for i below 10000 
            for loc = (random 100) collect (pick-phrase loc))))




