package com.oneisall.DoTasks;

import android.os.AsyncTask;
import android.support.v7.app.AppCompatActivity;
import android.os.Bundle;
import android.support.v7.widget.LinearLayoutManager;
import android.support.v7.widget.RecyclerView;
import android.util.Log;
import android.view.View;
import android.widget.Button;
import android.widget.ImageView;
import android.widget.TextView;
import android.widget.Toast;

import com.bumptech.glide.Glide;
import com.oneisall.Api.TaskApi;
import com.oneisall.DoTasks.Adapters.QuestionsAdapter;
import com.oneisall.Model.SubTaskDetail;
import com.oneisall.Model.TaskInfo;
import com.oneisall.Model.TaskRequest;
import com.oneisall.R;

import java.util.ArrayList;
import java.util.List;

import static com.oneisall.Constants.UrlConstants.MEDIA_BASE;

public class QuestionsActivity extends AppCompatActivity implements  View.OnClickListener {

    private static final String TAG = "QuestionsTask";
    private Button mPreSub;
    private Button mNextSub;
    private TextView mProg;
    private ImageView mImgSub;
    private RecyclerView mRecycle;
    //stl
    private List<String> mPaths = new ArrayList<String>();
    private int pathId = -1;
    private List<String> mDatas=new ArrayList<String>();
    private List<String> mAns = new ArrayList<String>();
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_questions);
        //get all files
        GetTaskInfo task = new GetTaskInfo();
        task.setOnDataFinishedListener(new GetTaskInfo.OnDataFinishedListener() {
            @Override
            public void onDataSuccessfully(TaskInfo taskInfo) {
                List<SubTaskDetail> resultInfo = taskInfo.getResultArray();
                for(int i=0; i<resultInfo.size(); i++){
                    mPaths.add(MEDIA_BASE+resultInfo.get(i).getFields().getFile());
                    Log.i(TAG, mPaths.get(i));
                }
                initView();
            }

            @Override
            public void onDataFailed() {
                Toast.makeText(QuestionsActivity.this, "获取信息失败", Toast.LENGTH_SHORT).show();
                Log.i(TAG, "获取信息失败");
            }
        });
        task.execute();
    }
    @Override
    public void onClick(View v){
        switch (v.getId()){
            //上一张
            case R.id.previous_subtask:{
                if(pathId <= 0)
                    Toast.makeText(this,"no previous", Toast.LENGTH_SHORT).show();
                else{
                    Glide.with(this).load(mPaths.get(--pathId)).into(mImgSub);
                    mProg.setText((pathId+1)+"/"+mPaths.size());
                    Toast.makeText(QuestionsActivity.this, "previous", Toast.LENGTH_SHORT).show();
                }
                break;
            }
            //下一张
            case R.id.next_subtask: {
//                new GetTaskInfo().execute();
                if (pathId >= mPaths.size() - 1)
                    Toast.makeText(QuestionsActivity.this, "no next", Toast.LENGTH_SHORT).show();
                else {
                    Glide.with(this).load(mPaths.get(++pathId)).into(mImgSub);
                    mProg.setText((pathId+1)+"/"+mPaths.size());
                    Toast.makeText(QuestionsActivity.this, "next", Toast.LENGTH_SHORT).show();
                }
                break;
            }
        }
    }
    void initView(){
        //get instances
        mPreSub = (Button)findViewById(R.id.previous_subtask);
        mNextSub = (Button)findViewById(R.id.next_subtask);
        mProg = (TextView)findViewById(R.id.subtask_progress);
        mImgSub = (ImageView) findViewById(R.id.img_subtask);
        //on click listener
        mNextSub.setOnClickListener(this);
        mPreSub.setOnClickListener(this);
        Glide.with(this).load(mPaths.get(++pathId)).into(mImgSub);
        mProg.setText((pathId+1)+"/"+mPaths.size());
        //TODO: delete
        initDatas();
        Log.i(TAG, "init data");
        //recycle view
        QuestionsAdapter adapter = new QuestionsAdapter(mDatas,mAns,QuestionsActivity.this);
        mRecycle = (RecyclerView)findViewById(R.id.qa_recyle_view);
        mRecycle.setLayoutManager(new LinearLayoutManager(this));
        mRecycle.setAdapter(adapter);
        Log.i(TAG, "ok");
        //on changed,监听事件
        adapter.setOnAnswerItemChangedListener(new QuestionsAdapter.onAnswerItemListener() {
            @Override
            public void onAnswerChanged(View v, int pos, String ans) {
                mAns.set(pos, ans);
//                Toast.makeText(QuestionsActivity.this,ans, Toast.LENGTH_SHORT).show();
            }
        });
    }
    private void initDatas(){
        for(int i=0; i<10; i++){
            mDatas.add("Q"+i+": please answer");
            mAns.add("");
        }
    }

    //get info
    private static class GetTaskInfo extends AsyncTask<Void, Void, TaskInfo> {
        @Override
        protected TaskInfo doInBackground(Void... voids) {
            return TaskApi.getTaskInfo(new TaskRequest());
        }

        @Override
        protected void onPostExecute(TaskInfo taskInfo) {
            Log.i(TAG, "onPostExecute: " + taskInfo.getResultArray());
            if(taskInfo!=null){
                mDataFinishedListener.onDataSuccessfully(taskInfo);
            }
            else{
                mDataFinishedListener.onDataFailed();
            }
        }
        //
        OnDataFinishedListener mDataFinishedListener;
        public void setOnDataFinishedListener(OnDataFinishedListener m){
            this.mDataFinishedListener = m;
        }
        //回调接口
        public interface OnDataFinishedListener {
            public void onDataSuccessfully(TaskInfo taskInfo);
            public void onDataFailed();
        }

        }
}